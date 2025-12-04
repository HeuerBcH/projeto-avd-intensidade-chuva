#!/bin/bash

echo ""
echo "🛑 Parando serviços do pipeline..."
echo ""

docker compose down

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Serviços parados com sucesso!"
    echo ""
    echo "💡 Para iniciar novamente, execute: ./start.sh"
else
    echo ""
    echo "⚠️  Alguns serviços podem não ter sido parados corretamente."
fi

echo ""
