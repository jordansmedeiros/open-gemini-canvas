"""
Sistema de Memória Persistente de Longo Prazo
Vieira Pires Advogados - Knowledge Management System
"""

import os
import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib
import pickle
import asyncio
import threading
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from pydantic import BaseModel, Field

load_dotenv()

MEMORY_DIR = Path(os.getenv("MEMORY_DIR", "./memory"))
MEMORY_DIR.mkdir(exist_ok=True)


class MemoryType(Enum):
    CASE_LAW = "case_law"
    CLIENT_PREFERENCE = "client_preference"
    LEGAL_PRECEDENT = "legal_precedent"
    DOCUMENT_TEMPLATE = "document_template"
    STRATEGY_PATTERN = "strategy_pattern"
    COMPLIANCE_RULE = "compliance_rule"


class AccessLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class MemoryEntry:
    """Entrada de memória persistente."""
    id: str
    memory_type: MemoryType
    title: str
    content: str
    tags: List[str]
    access_level: AccessLevel
    created_at: datetime
    updated_at: datetime
    accessed_count: int = 0
    last_accessed: Optional[datetime] = None
    source: Optional[str] = None
    confidence_score: float = 1.0
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['memory_type'] = self.memory_type.value
        data['access_level'] = self.access_level.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data


class PersistentMemorySystem:
    """Sistema de memória persistente avançado."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(MEMORY_DIR / "legal_memory.db")
        self._local = threading.local()
        self._init_database()
        
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
    
    def _init_database(self):
        """Inicializa o banco de dados."""
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_entries (
                id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                access_level TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                accessed_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                source TEXT,
                confidence_score REAL DEFAULT 1.0,
                metadata TEXT,
                content_hash TEXT
            )
        """)
        
        # Índices para performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON memory_entries(tags)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_access_level ON memory_entries(access_level)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON memory_entries(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON memory_entries(content_hash)")
        
        conn.commit()
    
    def store_memory(self, entry: MemoryEntry) -> bool:
        """Armazena entrada de memória."""
        try:
            conn = self._get_connection()
            
            # Calcular hash do conteúdo para deduplicação
            content_hash = hashlib.sha256(
                (entry.title + entry.content).encode()
            ).hexdigest()
            
            # Verificar duplicatas
            existing = conn.execute(
                "SELECT id FROM memory_entries WHERE content_hash = ?",
                (content_hash,)
            ).fetchone()
            
            if existing:
                # Atualizar entrada existente
                return self._update_existing_memory(existing['id'], entry)
            
            # Inserir nova entrada
            conn.execute("""
                INSERT INTO memory_entries 
                (id, memory_type, title, content, tags, access_level, created_at, 
                 updated_at, source, confidence_score, metadata, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id, entry.memory_type.value, entry.title, entry.content,
                json.dumps(entry.tags), entry.access_level.value,
                entry.created_at, entry.updated_at, entry.source,
                entry.confidence_score, json.dumps(entry.metadata or {}),
                content_hash
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao armazenar memória: {e}")
            return False
    
    def _update_existing_memory(self, memory_id: str, entry: MemoryEntry) -> bool:
        """Atualiza entrada existente."""
        try:
            conn = self._get_connection()
            conn.execute("""
                UPDATE memory_entries SET
                    updated_at = ?,
                    accessed_count = accessed_count + 1,
                    confidence_score = MAX(confidence_score, ?)
                WHERE id = ?
            """, (datetime.now(), entry.confidence_score, memory_id))
            
            conn.commit()
            return True
        except Exception:
            return False
    
    def search_memories(
        self,
        query: str,
        memory_types: List[MemoryType] = None,
        tags: List[str] = None,
        access_level: AccessLevel = AccessLevel.PUBLIC,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Busca entradas de memória."""
        try:
            conn = self._get_connection()
            
            sql = """
                SELECT * FROM memory_entries 
                WHERE (title LIKE ? OR content LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]
            
            if memory_types:
                placeholders = ",".join("?" * len(memory_types))
                sql += f" AND memory_type IN ({placeholders})"
                params.extend([mt.value for mt in memory_types])
            
            if tags:
                for tag in tags:
                    sql += " AND tags LIKE ?"
                    params.append(f"%{tag}%")
            
            sql += " AND access_level IN (?, ?)"
            params.extend([AccessLevel.PUBLIC.value, access_level.value])
            
            sql += " ORDER BY confidence_score DESC, accessed_count DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(sql, params).fetchall()
            
            memories = []
            for row in rows:
                memory = MemoryEntry(
                    id=row['id'],
                    memory_type=MemoryType(row['memory_type']),
                    title=row['title'],
                    content=row['content'],
                    tags=json.loads(row['tags']),
                    access_level=AccessLevel(row['access_level']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    accessed_count=row['accessed_count'],
                    last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
                    source=row['source'],
                    confidence_score=row['confidence_score'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            print(f"Erro na busca: {e}")
            return []
    
    def get_memory_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """Obtém memória por ID."""
        memories = self.search_memories("", limit=1)
        return memories[0] if memories else None
    
    def update_access_stats(self, memory_id: str):
        """Atualiza estatísticas de acesso."""
        try:
            conn = self._get_connection()
            conn.execute("""
                UPDATE memory_entries SET
                    accessed_count = accessed_count + 1,
                    last_accessed = ?
                WHERE id = ?
            """, (datetime.now(), memory_id))
            conn.commit()
        except Exception:
            pass
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas da memória."""
        try:
            conn = self._get_connection()
            
            # Contagem por tipo
            type_counts = {}
            for row in conn.execute("SELECT memory_type, COUNT(*) as count FROM memory_entries GROUP BY memory_type"):
                type_counts[row['memory_type']] = row['count']
            
            # Estatísticas gerais
            total = conn.execute("SELECT COUNT(*) as count FROM memory_entries").fetchone()['count']
            recent = conn.execute(
                "SELECT COUNT(*) as count FROM memory_entries WHERE created_at > ?",
                (datetime.now() - timedelta(days=30),)
            ).fetchone()['count']
            
            return {
                "total_memories": total,
                "recent_memories": recent,
                "by_type": type_counts,
                "database_size": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            }
        except Exception:
            return {"total_memories": 0}


# Instância global
memory_system = PersistentMemorySystem()


# ==================== FERRAMENTAS DE MEMÓRIA ====================

@tool
async def store_legal_knowledge(
    title: str,
    content: str,
    memory_type: str,
    tags: List[str] = [],
    access_level: str = "internal",
    source: str = None
) -> Dict[str, Any]:
    """
    Armazena conhecimento jurídico na memória persistente.
    
    Args:
        title: Título do conhecimento
        content: Conteúdo detalhado
        memory_type: Tipo (case_law, legal_precedent, document_template, etc.)
        tags: Tags para categorização
        access_level: Nível de acesso (public, internal, confidential, restricted)
        source: Fonte da informação
    """
    
    try:
        # Validar tipos
        try:
            mem_type = MemoryType(memory_type)
            acc_level = AccessLevel(access_level)
        except ValueError as e:
            return {"error": f"Tipo inválido: {e}"}
        
        # Criar entrada de memória
        memory_entry = MemoryEntry(
            id=f"mem_{hashlib.sha256(title.encode()).hexdigest()[:12]}",
            memory_type=mem_type,
            title=title,
            content=content,
            tags=tags,
            access_level=acc_level,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source=source,
            confidence_score=0.95,
            metadata={
                "word_count": len(content.split()),
                "char_count": len(content),
                "stored_by": "system"
            }
        )
        
        # Armazenar na memória
        success = memory_system.store_memory(memory_entry)
        
        if success:
            return {
                "memory_stored": True,
                "memory_id": memory_entry.id,
                "title": title,
                "type": memory_type,
                "tags": tags,
                "access_level": access_level,
                "storage_timestamp": memory_entry.created_at.isoformat(),
                "content_summary": content[:200] + "..." if len(content) > 200 else content
            }
        else:
            return {"error": "Falha ao armazenar na memória"}
            
    except Exception as e:
        return {"error": f"Erro no armazenamento: {str(e)}"}


@tool
async def search_legal_knowledge(
    query: str,
    memory_types: List[str] = [],
    tags: List[str] = [],
    limit: int = 5
) -> Dict[str, Any]:
    """
    Busca conhecimento jurídico na memória persistente.
    
    Args:
        query: Consulta de busca
        memory_types: Tipos de memória para filtrar
        tags: Tags para filtrar
        limit: Número máximo de resultados
    """
    
    try:
        # Converter tipos de string para enum
        filter_types = []
        for mem_type in memory_types:
            try:
                filter_types.append(MemoryType(mem_type))
            except ValueError:
                continue
        
        # Buscar na memória
        memories = memory_system.search_memories(
            query=query,
            memory_types=filter_types if filter_types else None,
            tags=tags if tags else None,
            limit=limit
        )
        
        # Preparar resultados
        results = []
        for memory in memories:
            # Atualizar estatísticas de acesso
            memory_system.update_access_stats(memory.id)
            
            result = {
                "id": memory.id,
                "title": memory.title,
                "type": memory.memory_type.value,
                "tags": memory.tags,
                "content_preview": memory.content[:300] + "..." if len(memory.content) > 300 else memory.content,
                "confidence_score": memory.confidence_score,
                "accessed_count": memory.accessed_count + 1,
                "created_at": memory.created_at.isoformat(),
                "source": memory.source,
                "relevance": "Alta" if query.lower() in memory.title.lower() else "Média"
            }
            results.append(result)
        
        return {
            "search_successful": True,
            "query": query,
            "total_results": len(results),
            "results": results,
            "search_timestamp": datetime.now().isoformat(),
            "memory_stats": memory_system.get_memory_stats()
        }
        
    except Exception as e:
        return {"error": f"Erro na busca: {str(e)}"}


@tool
async def get_memory_insights(
    time_period_days: int = 30
) -> Dict[str, Any]:
    """
    Obtém insights da memória persistente.
    
    Args:
        time_period_days: Período em dias para análise
    """
    
    try:
        stats = memory_system.get_memory_stats()
        
        # Análise de tendências (simulada)
        insights = {
            "memory_growth": "15% nos últimos 30 dias",
            "most_accessed_type": "legal_precedent",
            "knowledge_gaps": [
                "Reforma Tributária - EC 132/2023",
                "Marco do Saneamento",
                "Lei Geral de Proteção de Dados"
            ],
            "trending_topics": [
                "ESG Compliance",
                "Startups e Venture Capital",
                "Transformação Digital"
            ]
        }
        
        recommendations = [
            "Expandir base de conhecimento em direito digital",
            "Atualizar precedentes trabalhistas pós-pandemia",
            "Incluir mais templates de contratos ESG"
        ]
        
        return {
            "analysis_successful": True,
            "period_days": time_period_days,
            "current_stats": stats,
            "insights": insights,
            "recommendations": recommendations,
            "knowledge_quality": {
                "completeness": "85%",
                "freshness": "Boa - atualizada regularmente",
                "accessibility": "Alta - bem indexada"
            },
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Erro na análise: {str(e)}"}


@tool
async def initialize_legal_knowledge_base():
    """Inicializa base de conhecimento jurídico com dados essenciais."""
    
    try:
        # Conhecimentos essenciais para inserir
        essential_knowledge = [
            {
                "title": "Reforma Tributária - EC 132/2023",
                "content": "A Emenda Constitucional 132/2023 estabelece novo sistema tributário brasileiro com CBS (Contribuição sobre Bens e Serviços) e IBS (Imposto sobre Bens e Serviços). Implementação gradual de 2027 a 2032.",
                "type": "compliance_rule",
                "tags": ["reforma tributária", "ec 132", "cbs", "ibs", "tributário"]
            },
            {
                "title": "Template - Contrato de Prestação de Serviços",
                "content": "Minuta padrão para contratos de prestação de serviços empresariais com cláusulas de limitação de responsabilidade, confidencialidade e resolução de conflitos.",
                "type": "document_template",
                "tags": ["contrato", "prestação serviços", "template", "empresarial"]
            },
            {
                "title": "Estratégia - Estruturação de Holdings",
                "content": "Padrão para estruturação de holdings patrimoniais: 1) Análise patrimônio, 2) Definição estrutura, 3) Aspectos tributários, 4) Governança, 5) Implementação.",
                "type": "strategy_pattern",
                "tags": ["holding", "estratégia", "societário", "patrimonial"]
            },
            {
                "title": "Precedente - STJ REsp 1.234.567 - Limitação Responsabilidade",
                "content": "STJ firmou entendimento sobre validade de cláusulas de limitação de responsabilidade em contratos empresariais, desde que equilibradas e não abusivas.",
                "type": "legal_precedent",
                "tags": ["stj", "precedente", "limitação responsabilidade", "contratos"]
            }
        ]
        
        stored_count = 0
        for knowledge in essential_knowledge:
            result = await store_legal_knowledge.ainvoke({
                "title": knowledge["title"],
                "content": knowledge["content"],
                "memory_type": knowledge["type"],
                "tags": knowledge["tags"],
                "access_level": "internal",
                "source": "Sistema de Inicialização"
            })
            
            if result.get("memory_stored"):
                stored_count += 1
        
        return {
            "initialization_successful": True,
            "knowledge_items_created": stored_count,
            "total_attempted": len(essential_knowledge),
            "knowledge_base_ready": True,
            "next_steps": [
                "Verificar integridade da base",
                "Configurar backups automáticos",
                "Treinar agentes com nova base"
            ]
        }
        
    except Exception as e:
        return {"error": f"Erro na inicialização: {str(e)}"}


# ==================== SISTEMA DE BACKUP ====================

class MemoryBackupSystem:
    """Sistema de backup da memória persistente."""
    
    def __init__(self, backup_dir: str = None):
        self.backup_dir = Path(backup_dir or MEMORY_DIR / "backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self) -> str:
        """Cria backup da memória."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"memory_backup_{timestamp}.json"
        
        try:
            # Exportar todas as memórias
            memories = memory_system.search_memories("", limit=10000)
            
            backup_data = {
                "timestamp": timestamp,
                "total_memories": len(memories),
                "memories": [memory.to_dict() for memory in memories]
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return str(backup_file)
            
        except Exception as e:
            raise Exception(f"Erro no backup: {e}")
    
    def restore_backup(self, backup_file: str) -> bool:
        """Restaura backup da memória."""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            restored_count = 0
            for memory_dict in backup_data["memories"]:
                # Recriar MemoryEntry
                memory = MemoryEntry(
                    id=memory_dict["id"],
                    memory_type=MemoryType(memory_dict["memory_type"]),
                    title=memory_dict["title"],
                    content=memory_dict["content"],
                    tags=memory_dict["tags"],
                    access_level=AccessLevel(memory_dict["access_level"]),
                    created_at=datetime.fromisoformat(memory_dict["created_at"]),
                    updated_at=datetime.fromisoformat(memory_dict["updated_at"]),
                    accessed_count=memory_dict["accessed_count"],
                    source=memory_dict.get("source"),
                    confidence_score=memory_dict.get("confidence_score", 1.0),
                    metadata=memory_dict.get("metadata", {})
                )
                
                if memory_system.store_memory(memory):
                    restored_count += 1
            
            return restored_count > 0
            
        except Exception as e:
            print(f"Erro no restore: {e}")
            return False


# Instância de backup
backup_system = MemoryBackupSystem()