# Perícia — acompanhamento online privado

Interface web com plano de trabalho, biblioteca de documentos, pastas, quesitos, diário e relatório para impressão/PDF. O código fica neste repositório; os documentos e os dados do caso ficam em um volume privado no servidor, fora do Git.

## Publicar

[Abrir configuração de publicação no Render](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fanielneto-source%2Fpericia_teste)

O arquivo `render.yaml` configura uma aplicação Docker no Render com disco persistente de 1 GB. O serviço e o disco usam recursos pagos: confira os valores apresentados pelo Render antes de criar a infraestrutura. Não use armazenamento temporário para os documentos e o acompanhamento.

1. No Render, conecte sua conta GitHub e crie um **Blueprint** a partir deste repositório.
2. Defina `APP_PASSWORD` com uma senha exclusiva de pelo menos 16 caracteres. `SECRET_KEY` é gerada automaticamente.
3. Confira plano/custos e execute a publicação.
4. Abra a URL HTTPS informada pelo Render, entre com sua senha e importe o arquivo `Pacote_privado_pericia.zip`, gerado localmente por `exportar_pacote_online.py`.
5. Acesse o mesmo link em outros dispositivos. Os dados são gravados no servidor. O botão **Backup completo** exporta o acompanhamento e todos os arquivos.

Não envie o ZIP, PDFs, `.env`, notas ou backups para o repositório público. O pacote inicial é enviado somente pela tela autenticada, por HTTPS. A importação inicial não sobrescreve dados existentes. Guarde uma cópia do backup completo fora da hospedagem.

## Segurança e acesso

Todas as páginas, PDFs, textos, APIs e backups exigem autenticação. `/healthz` informa somente a disponibilidade. A sessão dura até oito horas; os cookies são HttpOnly, SameSite e Secure em produção. Alterações exigem token CSRF, e tentativas de senha têm limite de frequência. Use uma senha forte e HTTPS. Esta versão possui uma conta compartilhada do proprietário; não oferece cadastro de múltiplos usuários ou controle individual de permissões.

Um único processo Gunicorn usa oito threads e uma trava para gravação do estado. Mantenha `--workers 1` e uma única instância; não aumente réplicas sem migrar o armazenamento para banco de dados transacional. O disco persistente mantém os dados entre publicações. O último salvamento de um mesmo campo prevalece entre edições simultâneas.

## Executar localmente para desenvolvimento

Use Python 3.13 e instale `requirements.txt` (o Gunicorn é usado no Linux da hospedagem). Defina `APP_PASSWORD`, `SECRET_KEY`, `DATA_DIR` e, somente para desenvolvimento HTTP local, `COOKIE_SECURE=false`. Inicie com `flask --app app run`. Nunca use o servidor de desenvolvimento Flask para publicação.

Os testes de autenticação, importação, arquivos protegidos, persistência e backup usam o cliente de teste do Flask e um diretório temporário:

```text
python -m unittest discover -s tests -v
```

Os prazos e respostas exibidos vêm dos registros importados. O sistema não consulta o processo automaticamente nem calcula vencimentos processuais.
