# Drenagem urbana · Aparecida de Goiânia

Mapa interativo dos 18.796 registros de drenagem: 12.310 tampas de bueiro e 6.486 bocas de lobo. Filtros por tipo, bairro, rua e gravidade; busca textual; fichas completas com fotografias; exportação da seleção em GeoJSON.

Endereço previsto após ativar GitHub Pages: **https://anielneto-source.github.io/pericia_teste/**

## Publicação

O site está pronto na pasta `docs/`. Em **Settings → Pages**, use **Deploy from a branch**, branch **main**, pasta **/docs**, e salve. Não precisa de servidor Python, chave de API ou compilação para funcionar online.

O GitHub Pages precisa estar disponível para o plano e a visibilidade do repositório. A disponibilização do link depende de uma publicação concluída no GitHub Pages.

Os dados de navegação são carregados em GZIP (aproximadamente 1,6 MB), com alternativa GeoJSON sem compactação para navegadores sem suporte. Os downloads completos continuam disponíveis. As bibliotecas JavaScript estão no repositório; bases cartográficas e fotografias são serviços externos.

## Arquivos

- `docs/index.html`: mapa e filtros.
- `docs/drenagem_google_earth.kmz`: camada completa para Google Earth, com ícones incorporados e KML interno.
- `docs/pontos_interativos.svg`: desenho geográfico interativo independente, aberto no navegador.
- `docs/icones/`: símbolos SVG e PNG de cada tipo.
- `docs/drenagem.geojson`: camada completa em longitude/latitude WGS84.
- `docs/relatorio.json`: relatório de importação e contagens.
- `Planilha_Consolidada_Drenagem_COM_RUAS.xlsx`: planilha de origem.
- `gerar_mapa.py`: regeneração dos arquivos em `docs/` (`python -m pip install openpyxl pillow`).

O KML sem compactação excede 100 MB e não é versionado separadamente: seu conteúdo está no KMZ. Registros coincidentes são preservados. Detalhes dos dados, créditos das bases e instruções de uso local estão em [LEIA-ME.md](LEIA-ME.md).
