// Catálogo Chapeiro Shop — 6 coleções, 60 modelos, 2 variações cada (A/B).
// view: "frente" quando a prancha original mostra a frente, "costas" quando mostra as costas.
// O lado que não aparece na prancha é gerado (cor do tecido + assinatura discreta).
export const COLLECTIONS = {
  "basica-1":  { line: "Básica",  vol: "Vol. 01", title: "Essenciais da Pista" },
  "autoral-1": { line: "Autoral", vol: "Vol. 01", title: "Histórias da Chapa" },
  "premium-1": { line: "Premium", vol: "Vol. 01", title: "Edição de Estúdio" },
  "basica-2":  { line: "Básica",  vol: "Vol. 02", title: "Pequenas Histórias" },
  "autoral-2": { line: "Autoral", vol: "Vol. 02", title: "A Pista Vira História" },
  "premium-2": { line: "Premium", vol: "Vol. 02", title: "Arte para Vestir" },
};

const p = (code, name, collection, gender, type, desc, view = "frente", extra = {}) =>
  ({ code, name, collection, gender, type, desc, view, ...extra });

export const PRODUCTS = [
  p("B01", "Órbita", "basica-1", "unissex", "Camiseta regular gola careca", "Ícone Chapeiro em órbita no peito."),
  p("B02", "Assinatura", "basica-1", "unissex", "Camiseta oversized ombro caído", "Chapeiro centralizado em tipografia condensada."),
  p("B03", "Chapa 303", "basica-1", "unissex", "Camiseta com bolso gola careca", "Bolso no peito com estampa discreta 303."),
  p("B04", "Contorno", "basica-1", "unissex", "Camiseta ringer modelagem regular", "Detalhes em contraste e ícone em órbita no peito."),
  p("B05", "Dois Tempos", "basica-1", "unissex", "Camiseta raglan manga 3/4", "Estampa 303 no peito."),
  p("B06", "Pista Livre", "basica-1", "unissex", "Regata modelagem ampla", "Chapeiro no peito."),
  p("B07", "Primeira Fila", "basica-1", "feminino", "Baby tee ajustada, comprimento curto", "Ícone Chapeiro em órbita centralizado."),
  p("B08", "Quadro Curto", "basica-1", "unissex", "Camiseta cropped box, mangas largas", "Marca Chapeiro em quadro tipo HQ no peito."),
  p("B09", "Após o Set", "basica-1", "unissex", "Camiseta manga longa gola careca", "Ícone no peito e 303 discreto no punho."),
  p("B10", "Entre Amigos", "basica-1", "feminino", "Regata canelada ajustada, alças largas", "Pequeno ícone em órbita no peito."),

  p("A01", "Pedido 303", "autoral-1", "unissex", "Oversized tee · 100% algodão · silk", "Qual é o seu pedido, viajante?"),
  p("A02", "Último Palco", "autoral-1", "unissex", "Boxy tee · 100% algodão · silk nas costas", "Depois da última música, sempre tem chapa.", "costas"),
  p("A03", "Portal Aberto", "autoral-1", "unissex", "Camisa camp manga curta · estampa total", "Mesma chapa. Outras dimensões.", "frente", { allover: true }),
  p("A04", "Grave e Fome", "autoral-1", "unissex", "Regular tee · 100% algodão · silk", "O grave bateu. A fome respondeu."),
  p("A05", "Fora do Quadro", "autoral-1", "feminino", "Boxy cropped tee · 100% algodão · silk", "Às vezes o melhor rolê é o que escapa."),
  p("A06", "Frequência 303", "autoral-1", "unissex", "Jersey raglan · 100% poliéster · recortes costurados", "Mesma frequência em outros lugares."),
  p("A07", "Modo Avião", "autoral-1", "feminino", "Baby tee ajustada · 100% algodão · silk", "Desconecta pra conectar de verdade."),
  p("A08", "Vire a Página", "autoral-1", "unissex", "Manga longa · 100% algodão · silk", "Novos sons. Mesmas histórias."),
  p("A09", "Chapa Noturna", "autoral-1", "unissex", "Regata ampla · 100% algodão · silk", "5 da manhã. Ainda tem chapa."),
  p("A10", "Experiências", "autoral-1", "unissex", "Camisa bowling · recortes costurados", "Mesma chapa. Novos caminhos."),

  p("P01", "Órbita em Relevo", "premium-1", "unissex", "Tee boxy · ícone em relevo", "O ícone Chapeiro gravado no próprio tecido, tom sobre tom."),
  p("P02", "Comanda Ateliê", "premium-1", "unissex", "Tee pesada · etiqueta bordada", "Comanda 303 vertical no peito e pespontos aparentes."),
  p("P03", "Portal Jacquard", "premium-1", "unissex", "Camisa camp · jacquard", "Portais em órbita tecidos no jacquard, sem estampa.", "frente", { allover: true }),
  p("P04", "Linha Contínua", "premium-1", "unissex", "Tee com recortes e vivos", "Recortes curvos com vivo em contraste e ícone bordado."),
  p("P05", "Chapa Knit", "premium-1", "unissex", "Polo em tricô", "Listra dupla roxo e laranja com 303 bordado."),
  p("P06", "Madrugada", "premium-1", "unissex", "Suéter texturizado · cotoveleiras", "Textura em tricô, cotoveleiras e órbita bordada."),
  p("P07", "Quadro em Camadas", "premium-1", "unissex", "Tee sobreposta em camadas", "Duas camadas com barra em cor de contraste."),
  p("P08", "Contraluz", "premium-1", "unissex", "Tee com vivo diagonal", "Linhas em contraluz cruzando o peito."),
  p("P09", "Sobrecamada 303", "premium-1", "unissex", "Sobrecamisa · bolsos com lapela", "Etiqueta 303 no bolso e pespontos em laranja."),
  p("P10", "Portal Bordado", "premium-1", "unissex", "Tee boxy · bordado nas costas", "Portal pontilhado bordado à mão nas costas.", "costas"),

  p("B11", "Pausa na Chapa", "basica-2", "masculino", "Camiseta regular", "Disco, copo e sol: a pausa entre um set e outro."),
  p("B12", "Ponto de Encontro", "basica-2", "masculino", "Camiseta regular", "O mapa até a chapa 303."),
  p("B13", "Último Pedido", "basica-2", "masculino", "Camiseta com bolso", "A comanda do último pedido saindo do bolso."),
  p("B14", "Grave no Peito", "basica-2", "masculino", "Camiseta ringer", "A frigideira no ritmo do grave."),
  p("B15", "Amanhecer 303", "basica-2", "masculino", "Regata estonada", "O sol nascendo sobre a pista."),
  p("B16", "Entre uma Batida", "basica-2", "feminino", "Baby tee", "A conversa que acontece entre uma batida e outra."),
  p("B17", "Na Mesma Pista", "basica-2", "feminino", "Baby tee cropped", "Passos que viram sorriso."),
  p("B18", "Respiro", "basica-2", "feminino", "Regata canelada", "Um respiro no meio da pista."),
  p("B19", "Sol Depois do Set", "basica-2", "feminino", "Raglan cropped", "Depois do set, o sol."),
  p("B20", "Leva a História", "basica-2", "feminino", "Baby tee", "O ingresso que vira lembrança."),

  p("A11", "Onde a Noite Dobra", "autoral-2", "masculino", "Oversized tee · silk nas costas", "A estrada que leva da noite até a chapa.", "costas"),
  p("A12", "GPS da Galera", "autoral-2", "masculino", "Oversized tee", "Tô perto do som."),
  p("A13", "Servimos Encontros", "autoral-2", "masculino", "Camisa camp · painel estampado", "O balcão da chapa em meia camisa."),
  p("A14", "O Tempo Derrete", "autoral-2", "masculino", "Regata ampla", "Sem pressa."),
  p("A15", "Entre Frequências", "autoral-2", "masculino", "Manga longa", "A cena rasgada entre duas frequências."),
  p("A16", "Coragem de Ser Vista", "autoral-2", "feminino", "Tee boxy · silk nas costas", "Do seu jeito.", "costas"),
  p("A17", "Conversas de Outra Dimensão", "autoral-2", "feminino", "Baby tee", "A gente se encontra."),
  p("A18", "Janela para o Agora", "autoral-2", "feminino", "Regata cropped", "O pôr do sol visto da chapa."),
  p("A19", "O Rolê Continua", "autoral-2", "feminino", "Camisa · estampa total", "Caixas de som, ingressos e a chapa 303.", "frente", { allover: true }),
  p("A20", "Memórias em Movimento", "autoral-2", "feminino", "Tee · estampa em película", "A noite inteira num rolo de filme."),

  p("P11", "Cartografia da Madrugada", "premium-2", "masculino", "Tee pesada · estampa nas costas", "O mapa da madrugada até a 303.", "costas"),
  p("P12", "Além da Moldura", "premium-2", "masculino", "Camisa camp · estampa diagonal", "A cena que escapa da moldura."),
  p("P13", "Arquivo 303", "premium-2", "masculino", "Tee boxy · colagem", "Recortes de ingressos, discos e noites guardadas."),
  p("P14", "Som em Relevo", "premium-2", "masculino", "Manga longa", "Montanhas que são ondas sonoras."),
  p("P15", "Cena Inteira", "premium-2", "masculino", "Polo · estampa na barra", "A chapa ao pôr do sol, de ponta a ponta."),
  p("P16", "O que Floresce na Pista", "premium-2", "feminino", "Tee · estampa nas costas", "Discos que viram flores.", "costas"),
  p("P17", "Tempo de Sentir", "premium-2", "feminino", "Regata gola alta", "A ampulheta entre a pista e o amanhecer."),
  p("P18", "Fragmentos de um Encontro", "premium-2", "feminino", "Camisa camp · fotografias", "Fragmentos de um encontro na chapa."),
  p("P19", "Linhas que se Encontram", "premium-2", "feminino", "Baby tee", "Presença."),
  p("P20", "Portal de Memórias", "premium-2", "feminino", "Manga longa · faixa estampada", "Um portal de memórias em película."),
];
