# 🔧 Solução para Erro 403 no Trendz (refreshToken)

## ❌ Problema

Erro ao acessar Trendz:
```
:8888/apiTrendz/auth/refreshToken:1 Failed to load resource: the server responded with a status of 403 ()
```

## 🔍 Causa

O erro **403 (Forbidden)** no endpoint `/apiTrendz/auth/refreshToken` geralmente ocorre quando:

1. **Token JWT expirado**: O token de autenticação expirou e o refresh token também está inválido
2. **Sessão expirada**: A sessão do usuário no ThingsBoard expirou
3. **Problema de comunicação**: Trendz não consegue se comunicar corretamente com ThingsBoard
4. **Token inválido**: O token armazenado no navegador está corrompido ou inválido

## ✅ Soluções

### **Solução 1: Limpar Cache e Fazer Login Novamente** (Recomendado)

1. **Limpar cache do navegador**:
   - Pressione `Ctrl + Shift + Delete` (ou `Cmd + Shift + Delete` no Mac)
   - Selecione "Cookies e outros dados do site"
   - Clique em "Limpar dados"

2. **Ou limpar apenas para localhost:8888**:
   - Abra as DevTools (F12)
   - Vá em "Application" > "Storage"
   - Clique em "Clear site data"

3. **Recarregar a página**:
   - Pressione `Ctrl + F5` (ou `Cmd + Shift + R` no Mac) para recarregar sem cache

4. **Fazer login novamente**:
   - Acesse: http://localhost:8888
   - Faça login com as credenciais do ThingsBoard:
     - **Usuário**: `tenant@thingsboard.org`
     - **Senha**: `tenant`

---

### **Solução 2: Verificar Conexão Trendz ↔ ThingsBoard**

1. **Verificar se ThingsBoard está acessível**:
   ```bash
   curl http://localhost:9090/api/auth/login
   ```

2. **Verificar logs do Trendz**:
   ```bash
   docker logs trendz --tail 50
   ```

3. **Verificar logs do ThingsBoard**:
   ```bash
   docker logs thingsboard --tail 50
   ```

4. **Verificar se os containers estão na mesma rede**:
   ```bash
   docker network inspect projeto-avd-intensidade-chuva_avd-network
   ```

---

### **Solução 3: Reiniciar Containers**

Se o problema persistir, reinicie os containers:

```bash
# Parar containers
docker stop trendz thingsboard

# Iniciar containers
docker start thingsboard
# Aguardar 30 segundos para ThingsBoard inicializar
Start-Sleep -Seconds 30
docker start trendz

# Verificar logs
docker logs trendz --tail 20
docker logs thingsboard --tail 20
```

---

### **Solução 4: Verificar Configuração do Trendz**

Verifique se as variáveis de ambiente estão corretas no `docker-compose.yml`:

```yaml
environment:
  - TB_SERVER_URL=http://thingsboard:9090
  - TB_SERVER_WS_URL=ws://thingsboard:9090
  - TB_API_URL=http://thingsboard:9090
```

**Importante**: Use o nome do serviço Docker (`thingsboard`), não `localhost`!

---

### **Solução 5: Verificar Credenciais do ThingsBoard**

1. **Acesse ThingsBoard**: http://localhost:9090
2. **Faça login**:
   - Usuário: `tenant@thingsboard.org`
   - Senha: `tenant`
3. **Verifique se o login funciona**
4. **Depois, tente acessar Trendz novamente**: http://localhost:8888

---

## 🔍 Diagnóstico

### **Verificar Status dos Containers**

```bash
docker ps | Select-String -Pattern "trendz|thingsboard"
```

Ambos devem estar com status `Up`.

### **Testar Conexão ThingsBoard**

```bash
# Testar endpoint de login
curl -X POST http://localhost:9090/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"tenant@thingsboard.org","password":"tenant"}'
```

Se retornar um token, ThingsBoard está funcionando.

### **Testar Conexão Trendz**

```bash
# Verificar se Trendz está respondendo
curl http://localhost:8888
```

---

## 📝 Passos de Troubleshooting

1. ✅ **Limpar cache do navegador**
2. ✅ **Fazer logout e login novamente no Trendz**
3. ✅ **Verificar se ThingsBoard está acessível** (http://localhost:9090)
4. ✅ **Verificar logs** (`docker logs trendz` e `docker logs thingsboard`)
5. ✅ **Reiniciar containers** se necessário
6. ✅ **Verificar configuração** no `docker-compose.yml`

---

## ⚠️ Notas Importantes

1. **Token JWT**: Tokens JWT têm tempo de expiração. Se você ficar muito tempo sem usar, precisará fazer login novamente.

2. **Sessão**: A sessão no ThingsBoard pode expirar. Se isso acontecer, você precisará fazer login novamente no Trendz.

3. **Cache do Navegador**: O navegador pode estar usando um token antigo/inválido. Limpar o cache resolve na maioria dos casos.

4. **Rede Docker**: Certifique-se de que Trendz e ThingsBoard estão na mesma rede Docker (`avd-network`).

---

## 🚀 Solução Rápida (Mais Comum)

**Na maioria dos casos, a solução é simples:**

1. **Limpar cache do navegador** (Ctrl + Shift + Delete)
2. **Recarregar a página** (Ctrl + F5)
3. **Fazer login novamente** no Trendz

Isso resolve 90% dos casos de erro 403 no refreshToken.

---

## 📞 Se o Problema Persistir

Se nenhuma das soluções acima funcionar:

1. **Verifique os logs completos**:
   ```bash
   docker logs trendz > trendz.log
   docker logs thingsboard > thingsboard.log
   ```

2. **Verifique a configuração do docker-compose.yml**

3. **Verifique se há erros de rede**:
   ```bash
   docker exec trendz ping -c 3 thingsboard
   ```

4. **Reinicie todos os containers**:
   ```bash
   docker-compose -f projeto-avd-intensidade-chuva/docker-compose.yml restart trendz thingsboard
   ```

---

## ✅ Checklist de Verificação

- [ ] Cache do navegador limpo
- [ ] Login feito novamente no Trendz
- [ ] ThingsBoard acessível (http://localhost:9090)
- [ ] Containers rodando (`docker ps`)
- [ ] Logs sem erros críticos
- [ ] Configuração do docker-compose.yml correta
- [ ] Containers na mesma rede Docker

