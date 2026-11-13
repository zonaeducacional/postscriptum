# Post scriptum

**Um lugar para o que ficou por dizer.**

Caderno de fragmentos para escrever, reler e costurar textos. Os registros ficam na instalação local, sem conta, telemetria ou sincronização automática. Fontes Lora e Caveat incluídas no pacote.

- **PWA:** https://zonaeducacional.github.io/postscriptum/
- **Android:** [APK e checksum nas releases](https://github.com/zonaeducacional/postscriptum/releases).
- **Versão:** 0.1.0, protótipo de avaliação.

## Experiência

Fragmentos / Escrever / Costura. Exemplos separados na primeira utilização; escrita sem limite obrigatório; continuação vinculada; rascunho automático; edição com versões anteriores; lixeira e restauração. A Costura monta os fragmentos selecionados e permite acrescentar palavras antes de salvar um texto independente dos originais.

O banco é IndexedDB, com esquema versionado e transações. O aplicativo confirma gravação após a transação; em caso de falha, mostra o erro e preserva o texto em edição. Backups completos usam criptografia por senha e são validados antes de restaurar. O estado anterior à última restauração pode ser recuperado localmente.

## Executar localmente

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Abra http://127.0.0.1:8765. Não use `file://`. Dados pertencem ao endereço, porta e perfil do navegador; mudar a origem abre outro acervo. Use sempre a mesma origem ou transfira por backup.

## PWA e GitHub Pages

O workflow `.github/workflows/pages.yml` testa o app e publica os arquivos selecionados por `scripts/prepare_pages.py`. Configure **Settings → Pages → Source → GitHub Actions**. O pacote usa URLs relativas, compatíveis com `/postscriptum/`.

Abra o endereço HTTPS no celular e use Instalar / Adicionar à tela inicial. O service worker prepara o uso offline após o primeiro carregamento. Para atualizações de recursos, incremente a versão do cache em `sw.js`; a ativação espera as abas antigas fecharem. Não apague IndexedDB ao atualizar.

A hospedagem distribui o aplicativo; os textos não são enviados ao GitHub. O GitHub pode receber os acessos normais à hospedagem. A primeira instalação e atualizações usam rede.

## Android

APK independente, Android 8.0 ou superior, com Android System WebView atualizado. Os mesmos recursos web são incluídos no APK. Sem permissão de internet, de acesso amplo ao armazenamento, câmera, microfone ou contatos. O seletor de arquivos do Android controla a importação e exportação. A confirmação de exportação só ocorre depois que o arquivo foi gravado no destino escolhido; cancelar preserva o acervo.

O aplicativo bloqueia capturas de tela e a prévia dos registros na tela de aplicativos recentes. Backup automático e transferência de dados do sistema estão desativados; a transferência deve ser feita por backup explícito. PWA e APK não compartilham banco.

### Compilar

Requisitos: Python 3, JDK 21, Android SDK Platform 34 e Build Tools 34.0.0. O script usa AAPT2, javac, D8, zipalign e apksigner oficiais, sem dependências Android de terceiros.

```sh
python3 scripts/build_android.py --unsigned
```

Para uma release assinada, configure `POSTSCRIPTUM_KEYSTORE`, `POSTSCRIPTUM_STORE_PASSWORD` e, opcionalmente, `POSTSCRIPTUM_KEY_ALIAS` (padrão `postscriptum`), e execute:

```sh
python3 scripts/build_android.py
```

O APK e o SHA-256 são gravados em `releases/`, pasta ignorada pelo Git. Nunca versione a chave ou as senhas. Atualizações instaláveis sobre esta release precisam usar a mesma chave, o mesmo application ID e um versionCode maior.

A assinatura pública desta release tem SHA-256: `4706f7b5943b5003e7d2024f55da4566f009a41a9dbb93a89ddfa270b51ceea2`.

## Proteção e limites

**O banco ativo não tem criptografia própria nem PIN/biometria.** A proteção depende do aparelho e do perfil do navegador. O app é um protótipo, não um cofre auditado. Backup criptografado não equivale a criptografia do banco ativo.

Backups usam AES-256-GCM, PBKDF2-SHA-256 com 250.000 iterações e salt e IV aleatórios. A senha não é armazenada nem recuperável; escolha uma senha forte. O limite do arquivo de backup é 30 MB. Exportações `.txt` são texto aberto.

Faça backups fora do aplicativo. Limpar dados, remover a instalação ou perder o aparelho pode apagar registros. Armazenamento persistente, quando concedido pelo navegador, não substitui backup. Em falha de gravação, mantenha o app aberto e tente novamente ou baixe uma cópia de emergência.

O protótipo HTML anterior não é importado automaticamente. Backups antigos com comentários/notas são rejeitados para evitar descarte silencioso de conteúdo.

## Testes

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r tests/requirements.txt
python -m playwright install chromium
python tests/smoke.py
```

O teste usa dados fictícios e um servidor temporário no caminho `/postscriptum/`. Verifica rascunho após recarga, edição com versões, costura independente, lixeira, backup, rejeição de senha errada, restauração, uso offline, falha de gravação preservando texto e bloqueio entre abas. Também verifica o adaptador de exportação Android com uma ponte simulada e layouts de 360 e 390 px. Artefatos são temporários. Para outro executável Chromium, defina `CHROMIUM_PATH`.

O APK foi compilado, alinhado e teve a assinatura verificada. A primeira release não foi executada em aparelho Android físico ou emulador. Testar o seletor de arquivos, teclado, interrupção do processo e atualização instalada sobre a mesma assinatura continua necessário.

Licenças das fontes em `fonts/OFL-Lora.txt` e `fonts/OFL-Caveat.txt`.
