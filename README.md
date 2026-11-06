# Perícia — acompanhamento online privado

Interface web com plano de trabalho, biblioteca de documentos, pastas, quesitos, diário e relatório para impressão/PDF. O código fica neste repositório; os documentos e os dados do caso ficam em um volume privado no servidor, fora do Git.

## Endereço no GitHub Pages

Interface: **https://anielneto-source.github.io/pericia_teste/**.

Esta opção usa GitHub Pages para a interface e **Supabase Free** para login, documentos privados e sincronização. Os PDFs não são enviados ao GitHub. **[Guia de ativação do login e armazenamento](GUIA_GITHUB_PAGES.md)**.

O site pode ser publicado antes da conexão do projeto Supabase; nesse caso, ele mostra a tela de configuração. O acesso aos documentos só fica disponível depois de configurar o serviço privado e importar o pacote autenticado.

Para reconstruir os arquivos estáticos, execute `npm ci` e `npm run build:pages`. Para validar as transações e o isolamento de usuários: `npm run test:pages-sql`.

## Alternativa gratuita com servidor Python

A opção principal é o **PythonAnywhere Beginner/Free**, com armazenamento em disco e uma aplicação Python. A versão gratuita oferece 512 MiB de espaço e exige renovar a validade da aplicação pelo painel a cada mês. Consulte os limites atuais do serviço antes de usar.

**[Abrir o guia completo de publicação gratuita](GUIA_GRATUITO.md)** · [Criar conta gratuita](https://www.pythonanywhere.com/pricing/)

Após criar a conta, no console Bash do serviço:

```bash
git clone --depth 1 https://github.com/anielneto-source/pericia_teste.git ~/pericia_teste
cd ~/pericia_teste
python3.13 deploy/pythonanywhere_setup.py
```

O instalador pede a senha do sistema sem mostrá-la, guarda somente o hash em configuração privada e informa os caminhos para concluir a configuração WSGI no painel Web. Use a mesma versão de Python no instalador e na aplicação Web. Abra a URL HTTPS atribuída pelo serviço e importe o pacote privado pela tela autenticada.

Não envie o ZIP, PDFs, `.env`, notas ou backups para o repositório público. O pacote inicial é enviado somente pela tela autenticada, por HTTPS. A importação inicial não sobrescreve dados existentes. Guarde uma cópia do backup completo fora da hospedagem.

## Segurança e acesso

Todas as páginas, PDFs, textos, APIs e backups exigem autenticação. `/healthz` informa somente a disponibilidade. A sessão dura até oito horas; os cookies são HttpOnly, SameSite e Secure em produção. Alterações exigem token CSRF, e tentativas de senha têm limite de frequência. Use uma senha forte e HTTPS. Esta versão possui uma conta compartilhada do proprietário; não oferece cadastro de múltiplos usuários ou controle individual de permissões.

No PythonAnywhere, mantenha uma aplicação com um worker, conforme o plano gratuito. O aplicativo usa uma trava para gravação do estado em um único processo; não aumente réplicas sem migrar o armazenamento para banco de dados transacional. Os documentos ficam fora da pasta do código. O último salvamento de um mesmo campo prevalece entre edições simultâneas.

## Alternativa paga opcional

O Dockerfile e `deploy/render-opcional.yaml` preservam a opção de hospedagem no Render com serviço e disco pagos. Não são necessários para o PythonAnywhere. Nenhum plano pago é contratado pelo instalador gratuito.

## Executar localmente para desenvolvimento

Use Python 3.13 e instale `requirements.txt` (o Gunicorn é usado no Linux da hospedagem). Defina `APP_PASSWORD`, `SECRET_KEY`, `DATA_DIR` e, somente para desenvolvimento HTTP local, `COOKIE_SECURE=false`. Inicie com `flask --app app run`. Nunca use o servidor de desenvolvimento Flask para publicação.

Os testes de autenticação, importação, arquivos protegidos, persistência e backup usam o cliente de teste do Flask e um diretório temporário:

```text
python -m unittest discover -s tests -v
```

Os prazos e respostas exibidos vêm dos registros importados. O sistema não consulta o processo automaticamente nem calcula vencimentos processuais.
