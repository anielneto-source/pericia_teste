# Publicação gratuita no PythonAnywhere

Esta é a opção gratuita recomendada para a versão atual. O sistema mantém o login, os documentos privados e a gravação do acompanhamento no servidor, acessível de outros dispositivos. O código continua no GitHub público; os arquivos da perícia e as credenciais não entram no Git.

## Limites do plano gratuito

Conforme a documentação oficial consultada em 06/11/2026: **512 MiB de disco**, uma aplicação web com um worker e **validade de um mês**, renovável pelo painel. O espaço inclui bibliotecas e arquivos da conta. O pacote inicial desta perícia tem aproximadamente 7 MB comprimidos. Amplie o volume de fotografias com atenção ao espaço disponível e mantenha backups fora do serviço. Recursos e condições do plano podem mudar.

Fontes: [recursos da conta gratuita](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/), [planos](https://www.pythonanywhere.com/pricing/) e [configuração oficial do Flask](https://help.pythonanywhere.com/pages/Flask/).

## 1. Criar a conta gratuita

Abra https://www.pythonanywhere.com/pricing/ e escolha **Beginner / Free**. Você escolherá o usuário que compõe seu endereço. Nenhuma conta foi criada automaticamente por este projeto.

Na região padrão, a URL atribuída pelo serviço segue o formato `https://SEU_USUARIO.pythonanywhere.com`. Use a URL efetivamente exibida no painel Web; ela só estará ativa após a configuração.

## 2. Preparar o sistema

No painel **Consoles**, abra um console **Bash** e execute, uma linha por vez:

```bash
git clone --depth 1 https://github.com/anielneto-source/pericia_teste.git ~/pericia_teste
cd ~/pericia_teste
python3.13 deploy/pythonanywhere_setup.py
```

Use uma versão de Python disponível no painel (por exemplo, `python3.13`) e selecione a mesma versão ao criar a aplicação Web. O instalador cria um ambiente virtual, instala o Flask e pede uma senha exclusiva de pelo menos 16 caracteres, sem mostrá-la. A senha de acesso ao sistema é diferente da senha da sua conta PythonAnywhere.

O instalador salva somente o hash da senha e uma chave aleatória de sessão em `~/.config/pericia/config.json`, com acesso limitado ao usuário. Os documentos e os registros ficarão em `~/pericia-private`, separados do código. Reexecutar o instalador preserva os dados e a senha existentes.

## 3. Ativar a aplicação

1. Na aba **Web**, clique **Add a new web app**.
2. Selecione **Manual configuration** e a mesma versão de Python usada no instalador.
3. Em **Virtualenv**, informe `/home/SEU_USUARIO/.virtualenvs/pericia` (o instalador exibe o caminho exato).
4. Abra o link do arquivo de configuração **WSGI** e substitua seu conteúdo pelo conteúdo de `~/pericia_teste/deploy/pythonanywhere_wsgi.py`.
5. Deixe a seção **Static files** sem mapeamentos. PDFs, arquivos estáticos e APIs devem passar pela autenticação do aplicativo.
6. Ative **Force HTTPS**, salve e clique **Reload**.

## 4. Importar os documentos privados

Abra o endereço HTTPS exibido em **Web**, entre com a senha escolhida no instalador e envie o arquivo local `Pacote_privado_pericia.zip` pela página de importação. O arquivo já foi gerado na pasta principal do projeto no computador. Ele contém os 20 PDFs, o índice e os registros locais do acompanhamento na data da exportação. Não o envie ao repositório público.

Para exportar novamente os registros locais mais recentes, execute `python exportar_pacote_online.py` na pasta original do computador. A importação inicial só é permitida antes de existirem dados no servidor; ela não substitui registros existentes. Depois da importação, os dados local e online são independentes.

## Manter o serviço

- Renove a validade da aplicação pelo painel **Web** antes da data indicada pelo serviço.
- Use **Backup completo** no sistema e guarde uma cópia em outro local.
- Para atualizar o código, no Bash use `cd ~/pericia_teste`, depois `git pull --ff-only` e clique **Reload** no painel Web. Os arquivos privados ficam em outra pasta e são preservados.
- Para trocar a senha, execute `~/.virtualenvs/pericia/bin/python ~/pericia_teste/deploy/pythonanywhere_setup.py --change-password` e clique **Reload**. Para invalidar sessões já abertas, substitua também `SECRET_KEY` por uma nova chave aleatória no arquivo privado de configuração e recarregue.
- A hospedagem gratuita não oferece o mesmo nível de capacidade e disponibilidade de um plano dedicado. O sistema usa uma senha única de proprietário e não oferece contas individuais para outros usuários.

## Se a página não abrir

Confira o **Error log** na aba Web, a versão do Python e o caminho do virtualenv. A configuração WSGI deve apontar para o mesmo projeto preparado pelo instalador. Não execute `app.run()` ou `flask run` para publicar no PythonAnywhere; a aplicação é servida pela configuração WSGI do painel.
