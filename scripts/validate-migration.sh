#!/bin/bash

# OpenRouter Migration Validation Script
echo "🔍 Open Gemini Canvas - OpenRouter Migration Validation"
echo "======================================================"

# Check environment files
echo "📁 Checking environment configuration..."

if [ -f ".env.example" ]; then
    echo "✅ Root .env.example found"
else
    echo "❌ Root .env.example missing"
fi

if [ -f "agent/.env.example" ]; then
    echo "✅ Agent .env.example found"
else
    echo "❌ Agent .env.example missing"
fi

# Check if OpenRouter variables are in env examples
if grep -q "OPENROUTER_API_KEY" .env.example; then
    echo "✅ OpenRouter configuration found in root .env.example"
else
    echo "❌ OpenRouter configuration missing in root .env.example"
fi

if grep -q "OPENROUTER_API_KEY" agent/.env.example; then
    echo "✅ OpenRouter configuration found in agent .env.example"
else
    echo "❌ OpenRouter configuration missing in agent .env.example"
fi

echo ""
echo "🔧 Checking code migration..."

# Check if old Google imports are removed
if grep -q "google_genai\|google\.genai\|ChatGoogleGenerativeAI" agent/posts_generator_agent.py; then
    echo "⚠️  Warning: Old Google Gemini imports still present in posts_generator_agent.py"
else
    echo "✅ Posts generator agent successfully migrated to OpenRouter"
fi

if grep -q "google_genai\|google\.genai\|ChatGoogleGenerativeAI" agent/stack_agent.py; then
    echo "⚠️  Warning: Old Google Gemini imports still present in stack_agent.py"
else
    echo "✅ Stack analyzer agent successfully migrated to OpenRouter"
fi

# Check if new OpenAI imports are present
if grep -q "ChatOpenAI\|langchain_openai" agent/posts_generator_agent.py; then
    echo "✅ OpenRouter (OpenAI) imports found in posts generator"
else
    echo "❌ OpenRouter imports missing in posts generator"
fi

if grep -q "ChatOpenAI\|langchain_openai" agent/stack_agent.py; then
    echo "✅ OpenRouter (OpenAI) imports found in stack analyzer"
else
    echo "❌ OpenRouter imports missing in stack analyzer"
fi

# Check frontend migration
if grep -q "OpenAIAdapter" app/api/copilotkit/route.ts; then
    echo "✅ Frontend successfully migrated to OpenAIAdapter"
else
    echo "❌ Frontend still using GoogleGenerativeAIAdapter"
fi

echo ""
echo "📦 Checking dependencies..."

# Check pyproject.toml
if grep -q "openai" agent/pyproject.toml && grep -q "langchain-openai" agent/pyproject.toml; then
    echo "✅ OpenRouter dependencies added to pyproject.toml"
else
    echo "❌ OpenRouter dependencies missing in pyproject.toml"
fi

if grep -q "google-genai\|google-generativeai" agent/pyproject.toml; then
    echo "⚠️  Warning: Old Google dependencies still present in pyproject.toml"
else
    echo "✅ Old Google dependencies removed from pyproject.toml"
fi

echo ""
echo "📚 Checking documentation..."

if [ -f "OPENROUTER_SETUP.md" ]; then
    echo "✅ OpenRouter setup documentation created"
else
    echo "❌ OpenRouter setup documentation missing"
fi

if grep -q "OpenRouter" README.md; then
    echo "✅ README.md updated with OpenRouter information"
else
    echo "⚠️  README.md may need OpenRouter migration notes"
fi

echo ""
echo "🎯 Migration Summary:"
echo "==================="

# Count issues
issues=0

# Critical checks
if ! grep -q "OPENROUTER_API_KEY" .env.example; then
    issues=$((issues + 1))
fi

if ! grep -q "ChatOpenAI" agent/posts_generator_agent.py; then
    issues=$((issues + 1))
fi

if ! grep -q "ChatOpenAI" agent/stack_agent.py; then
    issues=$((issues + 1))
fi

if ! grep -q "OpenAIAdapter" app/api/copilotkit/route.ts; then
    issues=$((issues + 1))
fi

if [ $issues -eq 0 ]; then
    echo "🎉 SUCCESS: OpenRouter migration completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Copy .env.example to .env in both root and agent/ directories"
    echo "2. Add your OpenRouter API key to the .env files"
    echo "3. Run 'pnpm install' to install dependencies"
    echo "4. Run 'pnpm dev' to start the application"
    echo ""
    echo "🔗 Get your OpenRouter API key: https://openrouter.ai/"
else
    echo "❌ ISSUES FOUND: $issues critical issues need to be resolved"
    echo ""
    echo "Please review the warnings above and fix any missing components."
fi

echo ""
echo "📖 For detailed setup instructions, see: OPENROUTER_SETUP.md"