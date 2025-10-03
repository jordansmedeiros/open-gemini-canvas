"""
Sistema de Checkpointing Avançado
Este módulo implementa persistência de estado robusta para agentes LangGraph.
"""

import os
import json
import pickle
import sqlite3
import hashlib
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
import threading
import logging
from contextlib import contextmanager

from dotenv import load_dotenv
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

load_dotenv()

# ==================== CONFIGURAÇÃO ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHECKPOINT_DIR = Path(os.getenv("CHECKPOINT_DIR", "./checkpoints"))
CHECKPOINT_DIR.mkdir(exist_ok=True)


# ==================== ENUMS E TIPOS ====================

class CheckpointType(Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SCHEDULED = "scheduled"
    ERROR_RECOVERY = "error_recovery"
    MILESTONE = "milestone"


class CompressionType(Enum):
    NONE = "none"
    GZIP = "gzip"
    LZMA = "lzma"
    PICKLE = "pickle"


class StorageBackend(Enum):
    MEMORY = "memory"
    SQLITE = "sqlite"
    FILE = "file"
    REDIS = "redis"
    POSTGRESQL = "postgresql"


# ==================== MODELOS DE DADOS ====================

@dataclass
class CheckpointMetadata:
    """Metadados do checkpoint."""
    id: str
    session_id: str
    checkpoint_type: CheckpointType
    created_at: datetime
    size_bytes: int
    compression: CompressionType
    tags: List[str]
    description: Optional[str] = None
    parent_checkpoint_id: Optional[str] = None
    node_name: Optional[str] = None
    step_number: Optional[int] = None
    execution_time: Optional[float] = None
    memory_usage: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['checkpoint_type'] = self.checkpoint_type.value
        data['compression'] = self.compression.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointMetadata':
        """Cria instância a partir de dicionário."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['checkpoint_type'] = CheckpointType(data['checkpoint_type'])
        data['compression'] = CompressionType(data['compression'])
        return cls(**data)


class CheckpointConfig(BaseModel):
    """Configuração de checkpointing."""
    storage_backend: StorageBackend = StorageBackend.SQLITE
    auto_checkpoint_interval: int = 30  # segundos
    max_checkpoints_per_session: int = 100
    compression_enabled: bool = True
    compression_type: CompressionType = CompressionType.GZIP
    retention_days: int = 30
    enable_incremental: bool = True
    enable_compression_threshold: int = 1024  # bytes
    backup_enabled: bool = True
    encryption_enabled: bool = False


# ==================== STORAGE BACKENDS ====================

class SQLiteCheckpointStorage:
    """Backend de armazenamento SQLite para checkpoints."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(CHECKPOINT_DIR / "checkpoints.db")
        self._local = threading.local()
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtém conexão thread-safe."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def _init_db(self):
        """Inicializa o banco de dados."""
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                checkpoint_type TEXT NOT NULL,
                data BLOB NOT NULL,
                metadata TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                size_bytes INTEGER NOT NULL,
                compression TEXT NOT NULL,
                tags TEXT,
                node_name TEXT,
                step_number INTEGER,
                parent_checkpoint_id TEXT,
                description TEXT,
                execution_time REAL,
                memory_usage INTEGER
            )
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id 
            ON checkpoints(session_id)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON checkpoints(created_at)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoint_type 
            ON checkpoints(checkpoint_type)
        """)
        
        conn.commit()
    
    def save_checkpoint(
        self, 
        checkpoint_id: str,
        session_id: str,
        data: bytes,
        metadata: CheckpointMetadata
    ) -> bool:
        """Salva um checkpoint."""
        try:
            conn = self._get_connection()
            metadata_json = json.dumps(metadata.to_dict())
            tags_json = json.dumps(metadata.tags)
            
            conn.execute("""
                INSERT OR REPLACE INTO checkpoints 
                (id, session_id, checkpoint_type, data, metadata, created_at, 
                 size_bytes, compression, tags, node_name, step_number, 
                 parent_checkpoint_id, description, execution_time, memory_usage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                checkpoint_id, session_id, metadata.checkpoint_type.value,
                data, metadata_json, metadata.created_at,
                metadata.size_bytes, metadata.compression.value,
                tags_json, metadata.node_name, metadata.step_number,
                metadata.parent_checkpoint_id, metadata.description,
                metadata.execution_time, metadata.memory_usage
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar checkpoint: {e}")
            return False
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[Tuple[bytes, CheckpointMetadata]]:
        """Carrega um checkpoint."""
        try:
            conn = self._get_connection()
            row = conn.execute(
                "SELECT data, metadata FROM checkpoints WHERE id = ?",
                (checkpoint_id,)
            ).fetchone()
            
            if row:
                data = row['data']
                metadata_dict = json.loads(row['metadata'])
                metadata = CheckpointMetadata.from_dict(metadata_dict)
                return data, metadata
                
            return None
            
        except Exception as e:
            logger.error(f"Erro ao carregar checkpoint: {e}")
            return None
    
    def list_checkpoints(
        self, 
        session_id: Optional[str] = None,
        checkpoint_type: Optional[CheckpointType] = None,
        limit: int = 100
    ) -> List[CheckpointMetadata]:
        """Lista checkpoints com filtros."""
        try:
            conn = self._get_connection()
            query = "SELECT metadata FROM checkpoints WHERE 1=1"
            params = []
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            if checkpoint_type:
                query += " AND checkpoint_type = ?"
                params.append(checkpoint_type.value)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            
            checkpoints = []
            for row in rows:
                metadata_dict = json.loads(row['metadata'])
                metadata = CheckpointMetadata.from_dict(metadata_dict)
                checkpoints.append(metadata)
            
            return checkpoints
            
        except Exception as e:
            logger.error(f"Erro ao listar checkpoints: {e}")
            return []
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Remove um checkpoint."""
        try:
            conn = self._get_connection()
            conn.execute("DELETE FROM checkpoints WHERE id = ?", (checkpoint_id,))
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao deletar checkpoint: {e}")
            return False
    
    def cleanup_old_checkpoints(self, retention_days: int = 30) -> int:
        """Remove checkpoints antigos."""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            conn = self._get_connection()
            
            cursor = conn.execute(
                "DELETE FROM checkpoints WHERE created_at < ?",
                (cutoff_date,)
            )
            
            conn.commit()
            return cursor.rowcount
            
        except Exception as e:
            logger.error(f"Erro ao limpar checkpoints antigos: {e}")
            return 0


# ==================== COMPRESSÃO ====================

class CompressionManager:
    """Gerenciador de compressão para checkpoints."""
    
    @staticmethod
    def compress(data: bytes, compression_type: CompressionType) -> bytes:
        """Comprime dados."""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.GZIP:
            import gzip
            return gzip.compress(data)
        elif compression_type == CompressionType.LZMA:
            import lzma
            return lzma.compress(data)
        elif compression_type == CompressionType.PICKLE:
            return pickle.dumps(data)
        else:
            raise ValueError(f"Tipo de compressão não suportado: {compression_type}")
    
    @staticmethod
    def decompress(data: bytes, compression_type: CompressionType) -> bytes:
        """Descomprime dados."""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.GZIP:
            import gzip
            return gzip.decompress(data)
        elif compression_type == CompressionType.LZMA:
            import lzma
            return lzma.decompress(data)
        elif compression_type == CompressionType.PICKLE:
            return pickle.loads(data)
        else:
            raise ValueError(f"Tipo de compressão não suportado: {compression_type}")


# ==================== CHECKPOINT SAVER AVANÇADO ====================

class AdvancedCheckpointSaver(BaseCheckpointSaver):
    """
    Checkpoint saver avançado com recursos empresariais.
    """
    
    def __init__(self, config: CheckpointConfig = None):
        self.config = config or CheckpointConfig()
        self.storage = self._init_storage()
        self.compression_manager = CompressionManager()
        self._auto_checkpoint_task = None
        
        # Iniciar auto-checkpointing se habilitado
        if self.config.auto_checkpoint_interval > 0:
            self._start_auto_checkpoint()
    
    def _init_storage(self):
        """Inicializa o backend de armazenamento."""
        if self.config.storage_backend == StorageBackend.SQLITE:
            return SQLiteCheckpointStorage()
        elif self.config.storage_backend == StorageBackend.MEMORY:
            return MemorySaver()
        else:
            raise ValueError(f"Backend não suportado: {self.config.storage_backend}")
    
    def _start_auto_checkpoint(self):
        """Inicia checkpointing automático."""
        async def auto_checkpoint_loop():
            while True:
                await asyncio.sleep(self.config.auto_checkpoint_interval)
                await self._perform_auto_checkpoint()
        
        self._auto_checkpoint_task = asyncio.create_task(auto_checkpoint_loop())
    
    async def _perform_auto_checkpoint(self):
        """Executa checkpoint automático."""
        # Implementar lógica de checkpoint automático baseado em sessões ativas
        logger.info("Executando checkpoint automático")
    
    def save_checkpoint(
        self,
        session_id: str,
        state: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.MANUAL,
        tags: List[str] = None,
        description: str = None,
        node_name: str = None,
        step_number: int = None,
        parent_checkpoint_id: str = None
    ) -> str:
        """
        Salva um checkpoint com metadados avançados.
        """
        # Gerar ID único
        checkpoint_id = self._generate_checkpoint_id(session_id, state)
        
        # Serializar estado
        state_bytes = pickle.dumps(state)
        
        # Aplicar compressão se necessário
        if (self.config.compression_enabled and 
            len(state_bytes) >= self.config.enable_compression_threshold):
            compressed_data = self.compression_manager.compress(
                state_bytes, self.config.compression_type
            )
            compression_type = self.config.compression_type
        else:
            compressed_data = state_bytes
            compression_type = CompressionType.NONE
        
        # Criar metadados
        metadata = CheckpointMetadata(
            id=checkpoint_id,
            session_id=session_id,
            checkpoint_type=checkpoint_type,
            created_at=datetime.now(),
            size_bytes=len(compressed_data),
            compression=compression_type,
            tags=tags or [],
            description=description,
            node_name=node_name,
            step_number=step_number,
            parent_checkpoint_id=parent_checkpoint_id
        )
        
        # Salvar no storage
        success = self.storage.save_checkpoint(
            checkpoint_id, session_id, compressed_data, metadata
        )
        
        if success:
            logger.info(f"Checkpoint salvo: {checkpoint_id} para sessão {session_id}")
            
            # Cleanup se necessário
            self._cleanup_old_checkpoints(session_id)
            
            return checkpoint_id
        else:
            raise RuntimeError(f"Falha ao salvar checkpoint: {checkpoint_id}")
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Carrega um checkpoint específico.
        """
        result = self.storage.load_checkpoint(checkpoint_id)
        
        if result:
            data, metadata = result
            
            # Descomprimir se necessário
            if metadata.compression != CompressionType.NONE:
                decompressed_data = self.compression_manager.decompress(
                    data, metadata.compression
                )
            else:
                decompressed_data = data
            
            # Deserializar estado
            state = pickle.loads(decompressed_data)
            
            logger.info(f"Checkpoint carregado: {checkpoint_id}")
            return state
        
        return None
    
    def list_checkpoints(
        self,
        session_id: Optional[str] = None,
        checkpoint_type: Optional[CheckpointType] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[CheckpointMetadata]:
        """
        Lista checkpoints com filtros avançados.
        """
        checkpoints = self.storage.list_checkpoints(
            session_id=session_id,
            checkpoint_type=checkpoint_type,
            limit=limit
        )
        
        # Filtrar por tags se especificado
        if tags:
            filtered_checkpoints = []
            for cp in checkpoints:
                if any(tag in cp.tags for tag in tags):
                    filtered_checkpoints.append(cp)
            checkpoints = filtered_checkpoints
        
        return checkpoints
    
    def create_milestone_checkpoint(
        self,
        session_id: str,
        state: Dict[str, Any],
        milestone_name: str,
        description: str = None
    ) -> str:
        """
        Cria um checkpoint de marco importante.
        """
        return self.save_checkpoint(
            session_id=session_id,
            state=state,
            checkpoint_type=CheckpointType.MILESTONE,
            tags=["milestone", milestone_name],
            description=description or f"Marco: {milestone_name}"
        )
    
    def rollback_to_checkpoint(
        self,
        checkpoint_id: str,
        create_backup: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Faz rollback para um checkpoint específico.
        """
        state = self.load_checkpoint(checkpoint_id)
        
        if state and create_backup:
            # Criar backup do estado atual antes do rollback
            self.save_checkpoint(
                session_id="rollback_backup",
                state=state,
                checkpoint_type=CheckpointType.ERROR_RECOVERY,
                tags=["rollback", "backup"],
                description=f"Backup antes do rollback para {checkpoint_id}"
            )
        
        return state
    
    def _generate_checkpoint_id(self, session_id: str, state: Dict[str, Any]) -> str:
        """Gera ID único para checkpoint."""
        content = f"{session_id}_{datetime.now().isoformat()}_{hash(str(state))}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _cleanup_old_checkpoints(self, session_id: str):
        """Remove checkpoints antigos para uma sessão."""
        if self.config.max_checkpoints_per_session <= 0:
            return
        
        checkpoints = self.storage.list_checkpoints(
            session_id=session_id,
            limit=1000  # Carregar mais para cleanup
        )
        
        if len(checkpoints) > self.config.max_checkpoints_per_session:
            # Manter milestones e remover os mais antigos
            milestones = [cp for cp in checkpoints if cp.checkpoint_type == CheckpointType.MILESTONE]
            regular = [cp for cp in checkpoints if cp.checkpoint_type != CheckpointType.MILESTONE]
            
            # Ordenar por data (mais antigos primeiro)
            regular.sort(key=lambda x: x.created_at)
            
            # Calcular quantos remover
            keep_regular = self.config.max_checkpoints_per_session - len(milestones)
            to_remove = regular[:-keep_regular] if keep_regular > 0 else regular
            
            # Remover checkpoints antigos
            for cp in to_remove:
                self.storage.delete_checkpoint(cp.id)
                logger.info(f"Checkpoint removido (limpeza): {cp.id}")
    
    def get_checkpoint_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtém estatísticas dos checkpoints."""
        checkpoints = self.storage.list_checkpoints(session_id=session_id, limit=1000)
        
        if not checkpoints:
            return {"total": 0}
        
        total_size = sum(cp.size_bytes for cp in checkpoints)
        by_type = {}
        for cp in checkpoints:
            type_name = cp.checkpoint_type.value
            if type_name not in by_type:
                by_type[type_name] = 0
            by_type[type_name] += 1
        
        compression_stats = {}
        for cp in checkpoints:
            comp_name = cp.compression.value
            if comp_name not in compression_stats:
                compression_stats[comp_name] = {"count": 0, "total_size": 0}
            compression_stats[comp_name]["count"] += 1
            compression_stats[comp_name]["total_size"] += cp.size_bytes
        
        return {
            "total": len(checkpoints),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_type": by_type,
            "compression_stats": compression_stats,
            "oldest": min(cp.created_at for cp in checkpoints).isoformat(),
            "newest": max(cp.created_at for cp in checkpoints).isoformat()
        }
    
    def cleanup_old_checkpoints(self, retention_days: int = None) -> int:
        """Remove checkpoints antigos globalmente."""
        days = retention_days or self.config.retention_days
        return self.storage.cleanup_old_checkpoints(days)


# ==================== DECORADORES UTILITÁRIOS ====================

def auto_checkpoint(
    checkpoint_type: CheckpointType = CheckpointType.AUTOMATIC,
    tags: List[str] = None,
    description: str = None
):
    """
    Decorador para checkpointing automático de funções.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Assumir que o primeiro argumento é o estado
            if args and isinstance(args[0], dict):
                state = args[0]
                session_id = state.get("session_id", "default")
                
                # Executar função
                result = await func(*args, **kwargs)
                
                # Criar checkpoint após execução
                saver = AdvancedCheckpointSaver()
                saver.save_checkpoint(
                    session_id=session_id,
                    state=result if isinstance(result, dict) else state,
                    checkpoint_type=checkpoint_type,
                    tags=tags or [func.__name__],
                    description=description or f"Auto-checkpoint de {func.__name__}",
                    node_name=func.__name__
                )
                
                return result
            else:
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# ==================== INSTÂNCIA GLOBAL ====================

# Configuração padrão
default_config = CheckpointConfig(
    storage_backend=StorageBackend.SQLITE,
    auto_checkpoint_interval=60,  # 1 minuto
    max_checkpoints_per_session=50,
    compression_enabled=True,
    retention_days=7,
    enable_incremental=True
)

# Instância global
advanced_checkpoint_saver = AdvancedCheckpointSaver(default_config)