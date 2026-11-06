# Drenagem de Aparecida de Goiânia

Abra **iniciar_mapa.cmd** com duplo clique. O mapa será servido em **http://localhost:8879**. Mantenha a janela do servidor aberta; use Ctrl+C para encerrá-lo. Requer Python 3 (já disponível nesta máquina). O servidor atende apenas nesta máquina.

- **docs/drenagem_google_earth.kmz**: abra no Google Earth, preferencialmente Google Earth Pro para o conjunto completo. Possui pastas por tipo, símbolos próprios e fichas com todos os atributos. As imagens dos símbolos estão dentro do pacote; as fotografias são links externos.
- **docs/pontos_interativos.svg**: abra diretamente no navegador. Passe o mouse para uma descrição ou clique/pressione Enter no ponto para a ficha lateral com rolagem. Use o zoom do navegador para ampliar. É um desenho geográfico sem mapa de fundo; as posições usam projeção local aproximada para visualização. Visualizadores de imagem podem não executar a interação; use um navegador.
- **docs/icones/**: símbolos SVG originais para tampa de bueiro e boca de lobo, além de versões PNG compatíveis com Google Earth.
- **docs/drenagem.geojson**: camada de pontos com os atributos originais, longitude/latitude interpretadas como WGS84 (EPSG:4326). Pode ser aberta em QGIS e outros SIGs.
- **docs/drenagem.kml**: alternativa sem compactação ao KMZ. Mantenha a pasta `icones` junto dele.
- **docs/relatorio.json**: contagens e resultado das verificações de importação.

Foram usados os 18.796 registros da aba `Resultados`, classificados pela coluna `nombre_falla`: **12.310 Tampas de Bueiro** e **6.486 Bocas de Lobo**. As variações de maiúsculas foram unificadas em `tipo`; `nombre_falla` permanece original. Nenhuma coordenada inválida foi encontrada. Os limites são longitude -49,384880 a -49,2390838 e latitude -16,846730 a -16,7262395. Há 2.016 ocorrências adicionais em coordenadas repetidas; nenhum registro foi eliminado ou deslocado. O número da linha da planilha identifica cada registro, pois IDs de campo podem se repetir.

O mapa agrupa os pontos e separa os coincidentes ao ampliar/clicar no agrupamento. Oferece filtros por tipo, bairro, rua e gravidade, busca textual em todos os campos e exportação da seleção em GeoJSON. As contagens acompanham os filtros; o KMZ e o SVG disponíveis para download contêm a camada completa.

A base híbrida usa os serviços públicos Esri World Imagery, World Transportation e World Boundaries and Places, sem chave de API. Há alternativa OpenStreetMap no controle de camadas. Créditos aparecem no mapa. Serviços externos podem mudar de disponibilidade e estão sujeitos às condições de seus provedores. Internet é necessária para as bases e fotos; bibliotecas e dados são locais. Não foi feito download de mosaicos para uso offline.

Fontes dos serviços: https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer e https://services.arcgisonline.com/ArcGIS/rest/services/Reference . Créditos: https://support.esri.com/en-us/knowledge-base/what-is-the-correct-way-to-cite-an-arcgis-online-basema-000012040 . Bibliotecas: Leaflet 1.9.4 (BSD-2-Clause) e Leaflet.markercluster 1.5.3 (MIT).

Alguns nomes de colunas/bairros já contêm caracteres substituídos (`�`) na planilha; eles foram preservados, sem adivinhar o texto original. As unidades dos campos de medidas não são declaradas pela planilha e não foram inferidas. As coordenadas não foram confrontadas com um limite municipal oficial, e as fotografias não foram verificadas individualmente.

Para regenerar os dados, mantenha a planilha na pasta original e execute `python gerar_mapa.py` (requer `openpyxl` e `pillow`). Os arquivos existentes de saída são atualizados. O mapa local não modifica a planilha.
