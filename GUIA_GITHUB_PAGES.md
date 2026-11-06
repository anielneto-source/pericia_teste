# GitHub Pages com login e dados privados

Endereço da interface: **https://anielneto-source.github.io/pericia_teste/**.

O GitHub Pages entrega somente a interface. O login, os documentos e os registros são armazenados em um projeto **Supabase Free**. Assim, o acompanhamento fica acessível em diferentes dispositivos sem tornar os PDFs públicos no GitHub.

## Ativar o armazenamento gratuito

1. Crie sua conta em https://supabase.com/dashboard e um projeto no plano **Free**. Guarde a senha do banco de dados; ela não é a senha do sistema e não deve ser colocada no site.
2. No **SQL Editor** do projeto, execute o conteúdo de [deploy/supabase.sql](deploy/supabase.sql). Isso cria a tabela privada, o bucket privado e as regras que limitam o acesso aos arquivos e registros do usuário autenticado.
3. Em **Authentication → Users**, crie seu usuário com e-mail e uma senha forte. Use a opção de confirmar o usuário no painel. Desative cadastros públicos em **Authentication → Sign In / Providers**, se não deseja permitir outros cadastros. O site não possui formulário de cadastro.
4. Copie a URL do projeto e a chave **publishable** (ou a chave legada **anon**) em **Connect / API Keys**. Nunca use `secret`, `service_role` ou a senha do banco no navegador.
5. Abra o site do GitHub Pages. Na primeira tela, informe a URL e a chave pública. Entre com o e-mail e senha criados na etapa 3.
6. Importe `Pacote_privado_pericia.zip` pela tela autenticada. O pacote já foi gerado no computador na pasta principal do projeto. Ele não deve ser enviado ao GitHub.

Para deixar a conexão pré-configurada em todos os dispositivos, preencha **somente a URL e a chave pública** em `docs/config.json` no repositório. Sem isso, informe a mesma conexão na primeira visita de cada dispositivo. A proteção vem das políticas do banco/Storage e da autenticação, não do sigilo dessa chave pública.

## Acesso e sincronização

- Todos os registros e arquivos são vinculados ao usuário autenticado. Entre com a mesma conta nos demais dispositivos.
- As sessões são guardadas no armazenamento da aba/navegador; a senha não é persistida pela interface.
- Alterações de tarefas e quesitos são aplicadas por transação no banco. O último salvamento de um mesmo campo prevalece.
- A importação inicial não sobrescreve um acompanhamento existente. Cada tentativa envia os arquivos para uma pasta exclusiva. Em caso de falha, arquivos incompletos podem ficar no Storage; confira o bucket no painel antes de repetir muitas vezes para não consumir a cota.
- Use **Backup completo** para baixar um ZIP com todos os documentos e o estado atual. Guarde uma cópia fora da hospedagem.
- O progresso local anterior não é sincronizado automaticamente com o online; a importação copia o estado do momento da exportação.

## Limites e disponibilidade

O Supabase Free inclui atualmente 500 MB de banco de dados e 1 GB de armazenamento de arquivos, com cotas de tráfego e demais limites. Projetos gratuitos podem ser pausados por inatividade. Consulte [os planos oficiais](https://supabase.com/pricing) antes de ativar; permaneça no plano Free para não contratar recursos pagos. O pacote inicial atual tem cerca de 7 MB comprimidos, mas fotografias futuras também consomem armazenamento e tráfego.

Fontes: [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), [Supabase Storage privado](https://supabase.com/docs/guides/storage/buckets/fundamentals), [controle de acesso](https://supabase.com/docs/guides/storage/security/access-control).

## Atualizar a interface

Os arquivos publicados ficam em `docs/`, com Pages configurado para a branch `main` e pasta `/docs`. O adaptador está em `deploy/pages-entry.js`. `docs/pages.js` é seu bundle com as bibliotecas Supabase e fflate; nenhuma chave secreta ou dado real faz parte dele. As licenças ficam em `docs/THIRD_PARTY_LICENSES.txt`.

Depois de editar a interface original em `public/`, execute o empacotamento descrito em `deploy/build-pages.mjs`, valide e envie as alterações para `main`. A versão Python continua disponível como alternativa, mas não é executada no GitHub Pages.
