
const { Firestore } = require('@google-cloud/firestore');

// Firestore 클라이언트 초기화
// GCP 환경에서는 자동으로 인증 정보를 찾습니다.
const db = new Firestore({
  projectId: 'knu-sungsu613',
  databaseId: '(default)',
});

// Firestore에 업로드할 데이터
const mediaData = {
    "US": {
        "name": "미국",
        "broadcasting": [
            {"name": "PBS", "type": "공영"},
            {"name": "NBC", "type": "민영"},
            {"name": "ABC", "type": "민영"},
            {"name": "CBS", "type": "민영"},
        ],
        "newspapers": [
            {"name": "The New York Times", "type": "민영"},
            {"name": "Washington Post", "type": "민영"},
        ],
    },
    "UK": {
        "name": "영국",
        "broadcasting": [
            {"name": "BBC", "type": "공영"},
            {"name": "Sky News", "type": "민영"},
        ],
        "newspapers": [
            {"name": "The Guardian", "type": "민영"},
            {"name": "The Times", "type": "민영"},
        ],
    },
    "FR": {
        "name": "프랑스",
        "broadcasting": [
            {"name": "France 2", "type": "공영"},
            {"name": "TF1", "type": "민영"},
            {"name": "France 24", "type": "공영"},
        ],
        "newspapers": [
            {"name": "Le Monde", "type": "민영"},
            {"name": "Le Figaro", "type": "민영"},
        ],
    },
    "DE": {
        "name": "독일",
        "broadcasting": [
            {"name": "ARD", "type": "공영"},
            {"name": "ZDF", "type": "공영"},
            {"name": "DW", "type": "공영"},
        ],
        "newspapers": [
            {"name": "Süddeutsche Zeitung", "type": "민영"},
            {"name": "Bild", "type": "민영"},
        ],
    },
    "JP": {
        "name": "일본",
        "broadcasting": [
            {"name": "NHK", "type": "공영"},
            {"name": "NTV", "type": "민영"},
        ],
        "newspapers": [
            {"name": "Asahi Shimbun", "type": "민영"},
            {"name": "Yomiuri Shimbun", "type": "민영"},
        ],
    },
    "CN": {
        "name": "중국",
        "broadcasting": [
            {"name": "CCTV", "type": "공영"},
            {"name": "CGTN", "type": "공영"},
        ],
        "newspapers": [
            {"name": "People's Daily", "type": "공영"},
            {"name": "인민일보", "type": "공영"},
        ],
    },
    "RU": {
        "name": "러시아",
        "broadcasting": [
            {"name": "Первый канал", "type": "공영"},
            {"name": "Россия-1", "type": "공영"},
            {"name": "RT", "type": "공영"},
        ],
        "newspapers": [
            {"name": "Izvestia", "type": "민영"},
            {"name": "Kommersant", "type": "민영"},
        ],
    },
    "CA": {
        "name": "캐나다",
        "broadcasting": [
            {"name": "CBC", "type": "공영"},
            {"name": "Radio-Canada", "type": "공영"},
            {"name": "CTV", "type": "민영"},
        ],
        "newspapers": [
            {"name": "The Globe and Mail", "type": "민영"},
            {"name": "Toronto Star", "type": "민영"},
        ],
    },
    "KR": {
        "name": "대한민국",
        "broadcasting": [
            {"name": "KBS", "type": "공영"},
            {"name": "MBC", "type": "공영"},
            {"name": "SBS", "type": "민영"},
        ],
        "newspapers": [
            {"name": "조선일보", "type": "민영"},
            {"name": "중앙일보", "type": "민영"},
            {"name": "한겨레", "type": "민영"},
            {"name": "경향신문", "type": "민영"},
            {"name": "연합뉴스", "type": "공영"},
        ],
    },
  "IT": {
    "name": "이탈리아",
    "broadcasting": [
      { "name": "Rai", "type": "공영" },
      { "name": "Mediaset", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Corriere della Sera", "type": "민영" },
      { "name": "La Repubblica", "type": "민영" }
    ]
  },
  "ES": {
    "name": "스페인",
    "broadcasting": [
      { "name": "RTVE (La 1)", "type": "공영" },
      { "name": "Antena 3", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El País", "type": "민영" },
      { "name": "El Mundo", "type": "민영" }
    ]
  },
  "AU": {
    "name": "호주",
    "broadcasting": [
      { "name": "ABC", "type": "공영" },
      { "name": "SBS", "type": "공영" },
      { "name": "Seven News", "type": "민영" }
    ],
    "newspapers": [
      { "name": "The Sydney Morning Herald", "type": "민영" },
      { "name": "The Age", "type": "민영" }
    ]
  },
  "BR": {
    "name": "브라질",
    "broadcasting": [
      { "name": "TV Globo", "type": "민영" },
      { "name": "RecordTV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "O Globo", "type": "민영" },
      { "name": "Folha de S.Paulo", "type": "민영" }
    ]
  },
  "CA": {
    "name": "캐나다",
    "broadcasting": [
      { "name": "CBC/Radio-Canada", "type": "공영" },
      { "name": "CTV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "The Globe and Mail", "type": "민영" },
      { "name": "Toronto Star", "type": "민영" }
    ]
  },
  "TR": {
    "name": "터키",
    "broadcasting": [
      { "name": "TRT", "type": "공영" },
      { "name": "Show TV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Hürriyet", "type": "민영" },
      { "name": "Sabah", "type": "민영" }
    ]
  },
  "SA": {
    "name": "사우디아라비아",
    "broadcasting": [
      { "name": "Al Ekhbariya", "type": "국영" },
      { "name": "Al Arabiya", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Arab News", "type": "민영" },
      { "name": "Okaz", "type": "민영" }
    ]
  },
  "AE": {
    "name": "아랍에미리트",
    "broadcasting": [
      { "name": "Dubai TV", "type": "국영" },
      { "name": "Abu Dhabi TV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Gulf News", "type": "민영" },
      { "name": "Khaleej Times", "type": "민영" }
    ]
  },
  "EG": {
    "name": "이집트",
    "broadcasting": [
      { "name": "Nile TV", "type": "국영" },
      { "name": "ERTU (Channel 1)", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Al-Ahram", "type": "국영" },
      { "name": "Al-Masry Al-Youm", "type": "민영" }
    ]
  },
  "ZA": {
    "name": "남아프리카공화국",
    "broadcasting": [
      { "name": "SABC", "type": "공영" },
      { "name": "eNCA", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Mail & Guardian", "type": "민영" },
      { "name": "The Star", "type": "민영" }
    ]
  },
  "NG": {
    "name": "나이지리아",
    "broadcasting": [
      { "name": "NTA", "type": "국영" },
      { "name": "Channels TV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "The Guardian (Nigeria)", "type": "민영" },
      { "name": "Vanguard", "type": "민영" }
    ]
  },
  "TH": {
    "name": "태국",
    "broadcasting": [
      { "name": "Thai PBS", "type": "공영" },
      { "name": "Channel 3", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Bangkok Post", "type": "민영" },
      { "name": "The Nation (Thailand)", "type": "민영" }
    ]
  },
  "ID": {
    "name": "인도네시아",
    "broadcasting": [
      { "name": "TVRI", "type": "공영" },
      { "name": "Metro TV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Kompas", "type": "민영" },
      { "name": "The Jakarta Post", "type": "민영" }
    ]
  },
  "SG": {
    "name": "싱가포르",
    "broadcasting": [
      { "name": "CNA (Channel NewsAsia)", "type": "공영" },
      { "name": "Channel 5", "type": "공영" }
    ],
    "newspapers": [
      { "name": "The Straits Times", "type": "민영" }
    ]
  },
  "PK": {
    "name": "파키스탄",
    "broadcasting": [
      { "name": "PTV", "type": "국영" },
      { "name": "Geo News", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Dawn", "type": "민영" },
      { "name": "The News International", "type": "민영" }
    ]
  },
  "BD": {
    "name": "방글라데시",
    "broadcasting": [
      { "name": "BTV", "type": "국영" },
      { "name": "ATN News", "type": "민영" }
    ],
    "newspapers": [
      { "name": "The Daily Star (Bangladesh)", "type": "민영" },
      { "name": "Prothom Alo", "type": "민영" }
    ]
  },
  "VN": {
    "name": "베트남",
    "broadcasting": [
      { "name": "VTV", "type": "국영" },
      { "name": "HTV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Tuổi Trẻ", "type": "국영" },
      { "name": "Thanh Niên", "type": "국영" }
    ]
  },
  "PH": {
    "name": "필리핀",
    "broadcasting": [
      { "name": "ABS-CBN", "type": "민영" },
      { "name": "GMA Network", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Philippine Daily Inquirer", "type": "민영" },
      { "name": "Manila Bulletin", "type": "민영" }
    ]
  },
  "MY": {
    "name": "말레이시아",
    "broadcasting": [
      { "name": "RTM", "type": "공영" },
      { "name": "TV3", "type": "민영" },
      { "name": "Astro Awani", "type": "민영" }
    ],
    "newspapers": [
      { "name": "The Star (Malaysia)", "type": "민영" },
      { "name": "New Straits Times", "type": "민영" }
    ]
  },
  "IL": {
    "name": "이스라엘",
    "broadcasting": [
      { "name": "KAN (IPBC)", "type": "공영" },
      { "name": "Channel 12 (Keshet)", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Haaretz", "type": "민영" },
      { "name": "Yedioth Ahronoth", "type": "민영" }
    ]
  },
  "IR": {
    "name": "이란",
    "broadcasting": [
      { "name": "IRIB", "type": "국영" },
      { "name": "Press TV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Tehran Times", "type": "국영" },
      { "name": "Kayhan", "type": "국영" }
    ]
  },
  "UA": {
    "name": "우크라이나",
    "broadcasting": [
      { "name": "UA:PBC (Suspilne)", "type": "공영" },
      { "name": "1+1", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Kyiv Post", "type": "민영" },
      { "name": "Ukrainska Pravda", "type": "민영" }
    ]
  },
  "GR": {
    "name": "그리스",
    "broadcasting": [
      { "name": "ERT", "type": "공영" },
      { "name": "SKAI TV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Kathimerini", "type": "민영" },
      { "name": "Ta Nea", "type": "민영" }
    ]
  },
  "NL": {
    "name": "네덜란드",
    "broadcasting": [
      { "name": "NOS (NPO)", "type": "공영" },
      { "name": "RTL Nederland", "type": "민영" }
    ],
    "newspapers": [
      { "name": "De Telegraaf", "type": "민영" },
      { "name": "NRC Handelsblad", "type": "민영" }
    ]
  },
  "BE": {
    "name": "벨기에",
    "broadcasting": [
      { "name": "VRT", "type": "공영" },
      { "name": "RTBF", "type": "공영" }
    ],
    "newspapers": [
      { "name": "Le Soir", "type": "민영" },
      { "name": "De Standaard", "type": "민영" }
    ]
  },
  "SE": {
    "name": "스웨덴",
    "broadcasting": [
      { "name": "SVT", "type": "공영" },
      { "name": "TV4", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Dagens Nyheter", "type": "민영" },
      { "name": "Aftonbladet", "type": "민영" }
    ]
  },
  "NO": {
    "name": "노르웨이",
    "broadcasting": [
      { "name": "NRK", "type": "공영" },
      { "name": "TV2", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Aftenposten", "type": "민영" },
      { "name": "VG", "type": "민영" }
    ]
  },
  "FI": {
    "name": "핀란드",
    "broadcasting": [
      { "name": "Yle", "type": "공영" },
      { "name": "MTV3", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Helsingin Sanomat", "type": "민영" },
      { "name": "Ilta-Sanomat", "type": "민영" }
    ]
  },
  "DK": {
    "name": "덴마크",
    "broadcasting": [
      { "name": "DR", "type": "공영" },
      { "name": "TV 2", "type": "공영" }
    ],
    "newspapers": [
      { "name": "Politiken", "type": "민영" },
      { "name": "Jyllands-Posten", "type": "민영" },
      { "name": "Berlingske", "type": "민영" }
    ]
  },
  "PT": {
    "name": "포르투갈",
    "broadcasting": [
      { "name": "RTP", "type": "공영" },
      { "name": "SIC", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Público", "type": "민영" },
      { "name": "Diário de Notícias", "type": "민영" }
    ]
  },
  "CH": {
    "name": "스위스",
    "broadcasting": [
      { "name": "SRG SSR", "type": "공영" }
    ],
    "newspapers": [
      { "name": "Neue Zürcher Zeitung", "type": "민영" },
      { "name": "Tages-Anzeiger", "type": "민영" }
    ]
  },
  "CZ": {
    "name": "체코",
    "broadcasting": [
      { "name": "Česká televize", "type": "공영" },
      { "name": "TV Nova", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Lidové noviny", "type": "민영" },
      { "name": "Právo", "type": "민영" }
    ]
  },
  "PL": {
    "name": "폴란드",
    "broadcasting": [
      { "name": "TVP", "type": "공영" },
      { "name": "Polsat", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Gazeta Wyborcza", "type": "민영" },
      { "name": "Rzeczpospolita", "type": "민영" }
    ]
  },
  "AT": {
    "name": "오스트리아",
    "broadcasting": [
      { "name": "ORF", "type": "공영" },
      { "name": "Puls 4", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Die Presse", "type": "민영" },
      { "name": "Der Standard", "type": "민영" }
    ]
  },
  "HU": {
    "name": "헝가리",
    "broadcasting": [
      { "name": "MTVA (M1 등)", "type": "공영" },
      { "name": "RTL Klub", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Népszava", "type": "민영" },
      { "name": "Magyar Nemzet", "type": "민영" }
    ]
  },
  "RO": {
    "name": "루마니아",
    "broadcasting": [
      { "name": "TVR", "type": "공영" },
      { "name": "Pro TV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Adevărul", "type": "민영" },
      { "name": "România Liberă", "type": "민영" }
    ]
  },
  "BG": {
    "name": "불가리아",
    "broadcasting": [
      { "name": "BNT", "type": "공영" },
      { "name": "bTV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "24 Chasa", "type": "민영" },
      { "name": "Trud", "type": "민영" }
    ]
  },
  "HR": {
    "name": "크로아티아",
    "broadcasting": [
      { "name": "HRT", "type": "공영" },
      { "name": "Nova TV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Jutarnji list", "type": "민영" },
      { "name": "Večernji list", "type": "민영" }
    ]
  },
  "SK": {
    "name": "슬로바키아",
    "broadcasting": [
      { "name": "RTVS", "type": "공영" },
      { "name": "TV Markíza", "type": "민영" }
    ],
    "newspapers": [
      { "name": "SME", "type": "민영" },
      { "name": "Pravda (Slovakia)", "type": "민영" }
    ]
  },
  "MX": {
    "name": "멕시코",
    "broadcasting": [
      { "name": "Televisa", "type": "민영" },
      { "name": "TV Azteca", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El Universal", "type": "민영" },
      { "name": "Reforma", "type": "민영" }
    ]
  },
  "CL": {
    "name": "칠레",
    "broadcasting": [
      { "name": "TVN", "type": "공영" },
      { "name": "Canal 13", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El Mercurio", "type": "민영" },
      { "name": "La Tercera", "type": "민영" }
    ]
  },
  "AR": {
    "name": "아르헨티나",
    "broadcasting": [
      { "name": "TV Pública", "type": "공영" },
      { "name": "Canal 13 (El Trece)", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Clarín", "type": "민영" },
      { "name": "La Nación", "type": "민영" }
    ]
  },
  "NZ": {
    "name": "뉴질랜드",
    "broadcasting": [
      { "name": "TVNZ", "type": "공영" },
      { "name": "Three", "type": "민영" }
    ],
    "newspapers": [
      { "name": "The New Zealand Herald", "type": "민영" },
      { "name": "Stuff", "type": "민영" }
    ]
  },
  "IE": {
    "name": "아일랜드",
    "broadcasting": [
      { "name": "RTÉ", "type": "공영" },
      { "name": "Virgin Media One", "type": "민영" }
    ],
    "newspapers": [
      { "name": "The Irish Times", "type": "민영" },
      { "name": "Irish Independent", "type": "민영" }
    ]
  },
  "IS": {
    "name": "아이슬란드",
    "broadcasting": [
      { "name": "RÚV", "type": "공영" }
    ],
    "newspapers": [
      { "name": "Morgunblaðið", "type": "민영" }
    ]
  },
  "KE": {
    "name": "케냐",
    "broadcasting": [
      { "name": "KBC", "type": "공영" },
      { "name": "Citizen TV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Daily Nation", "type": "민영" },
      { "name": "The Standard", "type": "민영" }
    ]
  },
  "GH": {
    "name": "가나",
    "broadcasting": [
      { "name": "GTV", "type": "공영" },
      { "name": "TV3 Ghana", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Daily Graphic", "type": "국영" },
      { "name": "Ghanaian Times", "type": "국영" }
    ]
  },
  "DZ": {
    "name": "알제리",
    "broadcasting": [
      { "name": "ENTV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "El Moudjahid", "type": "국영" },
      { "name": "El Watan", "type": "민영" }
    ]
  },
  "MA": {
    "name": "모로코",
    "broadcasting": [
      { "name": "Al Aoula (SNRT)", "type": "국영" },
      { "name": "2M TV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Al-Massae", "type": "민영" }
    ]
  },
  "TN": {
    "name": "튀니지",
    "broadcasting": [
      { "name": "Wataniya 1", "type": "국영" }
    ],
    "newspapers": [
      { "name": "La Presse de Tunisie", "type": "국영" }
    ]
  },
  "ET": {
    "name": "에티오피아",
    "broadcasting": [
      { "name": "Ethiopian Broadcasting Corporation (EBC)", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Addis Zemen", "type": "국영" }
    ]
  },
  "CO": {
    "name": "콜롬비아",
    "broadcasting": [
      { "name": "RCN Televisión", "type": "민영" },
      { "name": "Caracol Televisión", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El Tiempo", "type": "민영" }
    ]
  },
  "PE": {
    "name": "페루",
    "broadcasting": [
      { "name": "TV Perú", "type": "공영" },
      { "name": "América Televisión", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El Comercio (Peru)", "type": "민영" }
    ]
  },
  "VE": {
    "name": "베네수엘라",
    "broadcasting": [
      { "name": "Venezolana de Televisión", "type": "국영" },
      { "name": "Globovisión", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El Nacional", "type": "민영" }
    ]
  },
  "CU": {
    "name": "쿠바",
    "broadcasting": [
      { "name": "Cubavisión", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Granma", "type": "국영" }
    ]
  },
  "SGP": {
    "name": "싱가포르(대체 코드 예시)",
    "broadcasting": [
      { "name": "CNA (Channel NewsAsia)", "type": "공영" }
    ],
    "newspapers": [
      { "name": "The Straits Times", "type": "민영" }
    ]
  },
  "KE": {
    "name": "케냐",
    "broadcasting": [
      { "name": "KBC", "type": "공영" },
      { "name": "Citizen TV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Daily Nation", "type": "민영" },
      { "name": "The Standard", "type": "민영" }
    ]
  },
  "GH": {
    "name": "가나",
    "broadcasting": [
      { "name": "GTV", "type": "공영" },
      { "name": "TV3 Ghana", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Daily Graphic", "type": "국영" },
      { "name": "Ghanaian Times", "type": "국영" }
    ]
  },
  "DZ": {
    "name": "알제리",
    "broadcasting": [
      { "name": "ENTV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "El Moudjahid", "type": "국영" },
      { "name": "El Watan", "type": "민영" }
    ]
  },
  "MA": {
    "name": "모로코",
    "broadcasting": [
      { "name": "Al Aoula (SNRT)", "type": "국영" },
      { "name": "2M TV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Al-Massae", "type": "민영" }
    ]
  },
  "TN": {
    "name": "튀니지",
    "broadcasting": [
      { "name": "Wataniya 1", "type": "국영" }
    ],
    "newspapers": [
      { "name": "La Presse de Tunisie", "type": "국영" }
    ]
  },
  "ET": {
    "name": "에티오피아",
    "broadcasting": [
      { "name": "Ethiopian Broadcasting Corporation (EBC)", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Addis Zemen", "type": "국영" }
    ]
  },
  "CO": {
    "name": "콜롬비아",
    "broadcasting": [
      { "name": "RCN Televisión", "type": "민영" },
      { "name": "Caracol Televisión", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El Tiempo", "type": "민영" }
    ]
  },
  "PE": {
    "name": "페루",
    "broadcasting": [
      { "name": "TV Perú", "type": "공영" },
      { "name": "América Televisión", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El Comercio (Peru)", "type": "민영" }
    ]
  },
  "VE": {
    "name": "베네수엘라",
    "broadcasting": [
      { "name": "Venezolana de Televisión", "type": "국영" },
      { "name": "Globovisión", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El Nacional", "type": "민영" }
    ]
  },
  "CU": {
    "name": "쿠바",
    "broadcasting": [
      { "name": "Cubavisión", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Granma", "type": "국영" }
    ]
  },
  "NZ": {
    "name": "뉴질랜드",
    "broadcasting": [
      { "name": "TVNZ", "type": "공영" },
      { "name": "Three", "type": "민영" }
    ],
    "newspapers": [
      { "name": "The New Zealand Herald", "type": "민영" },
      { "name": "Stuff", "type": "민영" }
    ]
  },
  "IE": {
    "name": "아일랜드",
    "broadcasting": [
      { "name": "RTÉ", "type": "공영" },
      { "name": "Virgin Media One", "type": "민영" }
    ],
    "newspapers": [
      { "name": "The Irish Times", "type": "민영" },
      { "name": "Irish Independent", "type": "민영" }
    ]
  },
  "IS": {
    "name": "아이슬란드",
    "broadcasting": [
      { "name": "RÚV", "type": "공영" }
    ],
    "newspapers": [
      { "name": "Morgunblaðið", "type": "민영" }
    ]
  },
  "SGP": {
    "name": "싱가포르",
    "broadcasting": [
      { "name": "CNA (Channel NewsAsia)", "type": "공영" },
      { "name": "Channel 5", "type": "공영" }
    ],
    "newspapers": [
      { "name": "The Straits Times", "type": "민영" }
    ]
  },
  "MYS": {
    "name": "말레이시아",
    "broadcasting": [
      { "name": "RTM", "type": "공영" },
      { "name": "TV3", "type": "민영" },
      { "name": "Astro Awani", "type": "민영" }
    ],
    "newspapers": [
      { "name": "The Star (Malaysia)", "type": "민영" },
      { "name": "New Straits Times", "type": "민영" }
    ]
  },
  "KWT": {
    "name": "쿠웨이트",
    "broadcasting": [
      { "name": "Kuwait TV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Al-Qabas", "type": "민영" }
    ]
  },
  "QAT": {
    "name": "카타르",
    "broadcasting": [
      { "name": "Al Jazeera", "type": "국영" },
      { "name": "Qatar TV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Gulf Times", "type": "민영" }
    ]
  },
  "OMN": {
    "name": "오만",
    "broadcasting": [
      { "name": "Oman TV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Times of Oman", "type": "민영" }
    ]
  },
  "JOR": {
    "name": "요르단",
    "broadcasting": [
      { "name": "JRTV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Jordan Times", "type": "민영" },
      { "name": "Al Ra'i", "type": "국영" }
    ]
  },
  "KAZ": {
    "name": "카자흐스탄",
    "broadcasting": [
      { "name": "Qazaqstan TV", "type": "국영" },
      { "name": "Khabar TV", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Egemen Kazakhstan", "type": "국영" }
    ]
  },
  "GEO": {
    "name": "조지아",
    "broadcasting": [
      { "name": "GPB (1TV)", "type": "공영" },
      { "name": "Rustavi 2", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Sakartvelos Respublika", "type": "국영" }
    ]
  },
  "SRB": {
    "name": "세르비아",
    "broadcasting": [
      { "name": "RTS", "type": "공영" },
      { "name": "Prva TV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Politika (Serbia)", "type": "민영" },
      { "name": "Blic", "type": "민영" }
    ]
  },
  "SVN": {
    "name": "슬로베니아",
    "broadcasting": [
      { "name": "RTV Slovenija", "type": "공영" },
      { "name": "POP TV", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Delo", "type": "민영" }
    ]
  },
  "LTU": {
    "name": "리투아니아",
    "broadcasting": [
      { "name": "LRT", "type": "공영" }
    ],
    "newspapers": [
      { "name": "Lietuvos rytas", "type": "민영" }
    ]
  },
  "LVA": {
    "name": "라트비아",
    "broadcasting": [
      { "name": "LTV", "type": "공영" }
    ],
    "newspapers": [
      { "name": "Latvijas Avīze", "type": "민영" }
    ]
  },
  "EST": {
    "name": "에스토니아",
    "broadcasting": [
      { "name": "ERR", "type": "공영" }
    ],
    "newspapers": [
      { "name": "Postimees", "type": "민영" }
    ]
  },
  "ISL": {
    "name": "아이슬란드",
    "broadcasting": [
      { "name": "RÚV", "type": "공영" }
    ],
    "newspapers": [
      { "name": "Morgunblaðið", "type": "민영" }
    ]
  },
  "SA": {
    "name": "사우디아라비아",
    "broadcasting": [
      { "name": "Al Arabiya", "domain": "alarabiya.net", "type": "민영" },
      { "name": "Al Ekhbariya", "domain": "alekhbariya.net", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Arab News", "domain": "arabnews.com", "type": "민영" },
      { "name": "Saudi Gazette", "domain": "saudigazette.com.sa", "type": "민영" }
    ]
  },
  "AE": {
    "name": "아랍에미리트",
    "broadcasting": [
      { "name": "Al Arabiya", "domain": "alarabiya.net", "type": "민영" },
      { "name": "Dubai TV", "domain": "dubaitv.ae", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Gulf News", "domain": "gulfnews.com", "type": "민영" },
      { "name": "Khaleej Times", "domain": "khaleejtimes.com", "type": "민영" }
    ]
  },
  "IR": {
    "name": "이란",
    "broadcasting": [
      { "name": "Press TV", "domain": "presstv.ir", "type": "국영" },
      { "name": "IRIB News", "domain": "iribnews.ir", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Tehran Times", "domain": "tehrantimes.com", "type": "국영" },
      { "name": "Kayhan", "domain": "kayhan.ir", "type": "국영" }
    ]
  },
  "IL": {
    "name": "이스라엘",
    "broadcasting": [
      { "name": "i24NEWS", "domain": "i24news.tv", "type": "민영" },
      { "name": "Channel 12 News", "domain": "12news.co.il", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Haaretz", "domain": "haaretz.com", "type": "민영" },
      { "name": "The Jerusalem Post", "domain": "jpost.com", "type": "민영" }
    ]
  },
  "QA": {
    "name": "카타르",
    "broadcasting": [
      { "name": "Al Jazeera English", "domain": "aljazeera.com", "type": "국영" },
      { "name": "Al Jazeera Arabic", "domain": "aljazeera.net", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Gulf Times", "domain": "gulf-times.com", "type": "민영" },
      { "name": "The Peninsula", "domain": "thepeninsulaqatar.com", "type": "민영" }
    ]
  },
  "JO": {
    "name": "요르단",
    "broadcasting": [
      { "name": "JRTV", "domain": "jrtv.gov.jo", "type": "국영" }
    ],
    "newspapers": [
      { "name": "The Jordan Times", "domain": "jordantimes.com", "type": "민영" },
      { "name": "Al Ra'i", "domain": "alrai.com", "type": "국영" }
    ]
  },
  "KW": {
    "name": "쿠웨이트",
    "broadcasting": [
      { "name": "Kuwait TV", "domain": "media.gov.kw", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Kuwait Times", "domain": "kuwaittimes.com", "type": "민영" },
      { "name": "Al-Qabas", "domain": "alqabas.com", "type": "민영" }
    ]
  },
  "TH": {
    "name": "태국",
    "broadcasting": [
      { "name": "Thai PBS", "domain": "thaipbs.or.th", "type": "공영" },
      { "name": "Channel 3", "domain": "ch3plus.com", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Bangkok Post", "domain": "bangkokpost.com", "type": "민영" },
      { "name": "The Nation Thailand", "domain": "nationthailand.com", "type": "민영" }
    ]
  },
  "ID": {
    "name": "인도네시아",
    "broadcasting": [
      { "name": "Metro TV", "domain": "metrotvnews.com", "type": "민영" },
      { "name": "RCTI", "domain": "rctiplus.com", "type": "민영" }
    ],
    "newspapers": [
      { "name": "The Jakarta Post", "domain": "thejakartapost.com", "type": "민영" },
      { "name": "Kompas", "domain": "kompas.com", "type": "민영" }
    ]
  },
  "SG": {
    "name": "싱가포르",
    "broadcasting": [
      { "name": "CNA (Channel NewsAsia)", "domain": "channelnewsasia.com", "type": "공영" }
    ],
    "newspapers": [
      { "name": "The Straits Times", "domain": "straitstimes.com", "type": "민영" }
    ]
  },
  "VN": {
    "name": "베트남",
    "broadcasting": [
      { "name": "VTV", "domain": "vtv.vn", "type": "국영" },
      { "name": "HTV", "domain": "htv.com.vn", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Tuoi Tre News", "domain": "tuoitrenews.vn", "type": "국영" },
      { "name": "Thanh Nien News", "domain": "thanhniennews.com", "type": "국영" }
    ]
  },
  "PH": {
    "name": "필리핀",
    "broadcasting": [
      { "name": "ABS-CBN News", "domain": "news.abs-cbn.com", "type": "민영" },
      { "name": "GMA News", "domain": "gmanetwork.com", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Philippine Daily Inquirer", "domain": "inquirer.net", "type": "민영" },
      { "name": "Manila Bulletin", "domain": "mb.com.ph", "type": "민영" }
    ]
  },
  "MY": {
    "name": "말레이시아",
    "broadcasting": [
      { "name": "Astro Awani", "domain": "astroawani.com", "type": "민영" },
      { "name": "RTM (Berita RTM)", "domain": "rtm.gov.my", "type": "공영" }
    ],
    "newspapers": [
      { "name": "The Star", "domain": "thestar.com.my", "type": "민영" },
      { "name": "New Straits Times", "domain": "nst.com.my", "type": "민영" }
    ]
  },
  "ZA": {
    "name": "남아프리카공화국",
    "broadcasting": [
      { "name": "SABC News", "domain": "sabcnews.com", "type": "공영" },
      { "name": "eNCA", "domain": "enca.com", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Mail & Guardian", "domain": "mg.co.za", "type": "민영" },
      { "name": "News24", "domain": "news24.com", "type": "민영" }
    ]
  },
  "NG": {
    "name": "나이지리아",
    "broadcasting": [
      { "name": "Channels TV", "domain": "channelstv.com", "type": "민영" },
      { "name": "NTA", "domain": "nta.ng", "type": "국영" }
    ],
    "newspapers": [
      { "name": "The Guardian Nigeria", "domain": "guardian.ng", "type": "민영" },
      { "name": "Vanguard", "domain": "vanguardngr.com", "type": "민영" }
    ]
  },
  "KE": {
    "name": "케냐",
    "broadcasting": [
      { "name": "KBC", "domain": "kbc.co.ke", "type": "공영" },
      { "name": "Citizen TV", "domain": "citizen.digital", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Daily Nation", "domain": "nation.africa", "type": "민영" },
      { "name": "The Standard", "domain": "standardmedia.co.ke", "type": "민영" }
    ]
  },
  "EG": {
    "name": "이집트",
    "broadcasting": [
      { "name": "Nile News / Nile TV", "domain": "nileinternational.net", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Al-Ahram", "domain": "english.ahram.org.eg", "type": "국영" },
      { "name": "Ahram Online", "domain": "ahram.org.eg", "type": "국영" }
    ]
  },
  "DZ": {
    "name": "알제리",
    "broadcasting": [
      { "name": "ENTV (Télévision Algérienne)", "domain": "entv.dz", "type": "국영" }
    ],
    "newspapers": [
      { "name": "El Watan", "domain": "elwatan.com", "type": "민영" },
      { "name": "El Moudjahid", "domain": "elmoudjahid.com", "type": "국영" }
    ]
  },
  "BR": {
    "name": "브라질",
    "broadcasting": [
      { "name": "TV Globo / GloboNews", "domain": "g1.globo.com", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Folha de S.Paulo", "domain": "folha.uol.com.br", "type": "민영" },
      { "name": "O Globo", "domain": "oglobo.globo.com", "type": "민영" }
    ]
  },
  "MX": {
    "name": "멕시코",
    "broadcasting": [
      { "name": "Televisa / Noticieros Televisa", "domain": "noticieros.televisa.com", "type": "민영" },
      { "name": "TV Azteca", "domain": "tvazteca.com", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El Universal", "domain": "eluniversal.com.mx", "type": "민영" },
      { "name": "Reforma", "domain": "reforma.com", "type": "민영" }
    ]
  },
  "AR": {
    "name": "아르헨티나",
    "broadcasting": [
      { "name": "Todo Noticias (TN)", "domain": "tn.com.ar", "type": "민영" },
      { "name": "Canal 13 (El Trece)", "domain": "eltrecetv.com.ar", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Clarín", "domain": "clarin.com", "type": "민영" },
      { "name": "La Nación", "domain": "lanacion.com.ar", "type": "민영" }
    ]
  },
  "CL": {
    "name": "칠레",
    "broadcasting": [
      { "name": "TVN", "domain": "tvn.cl", "type": "공영" },
      { "name": "Canal 13", "domain": "13.cl", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El Mercurio", "domain": "emol.com", "type": "민영" },
      { "name": "La Tercera", "domain": "latercera.com", "type": "민영" }
    ]
  },
  "CO": {
    "name": "콜롬비아",
    "broadcasting": [
      { "name": "Caracol Televisión / Noticias Caracol", "domain": "caracoltv.com", "type": "민영" },
      { "name": "RCN Televisión", "domain": "canalrcn.com", "type": "민영" }
    ],
    "newspapers": [
      { "name": "El Tiempo", "domain": "eltiempo.com", "type": "민영" },
      { "name": "El Espectador", "domain": "elespectador.com", "type": "민영" }
    ]
  },
  "UA": {
    "name": "우크라이나",
    "broadcasting": [
      { "name": "Suspilne / UA:PBC", "domain": "suspilne.media", "type": "공영" },
      { "name": "1+1", "domain": "1plus1.ua", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Kyiv Independent", "domain": "kyivindependent.com", "type": "민영" },
      { "name": "Ukrainska Pravda", "domain": "pravda.com.ua", "type": "민영" }
    ]
  },
  "PL": {
    "name": "폴란드",
    "broadcasting": [
      { "name": "TVP Info", "domain": "tvp.info", "type": "공영" },
      { "name": "TVN24", "domain": "tvn24.pl", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Gazeta Wyborcza", "domain": "wyborcza.pl", "type": "민영" },
      { "name": "Rzeczpospolita", "domain": "rp.pl", "type": "민영" }
    ]
  },
  "CZ": {
    "name": "체코",
    "broadcasting": [
      { "name": "ČT24", "domain": "ct24.ceskatelevize.cz", "type": "공영" },
      { "name": "Nova TV", "domain": "tvnova.cz", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Lidové noviny", "domain": "lidovky.cz", "type": "민영" },
      { "name": "Mladá fronta DNES", "domain": "idnes.cz", "type": "민영" }
    ]
  },
  "KZ": {
    "name": "카자흐스탄",
    "broadcasting": [
      { "name": "Qazaqstan TV", "domain": "qazaqstan.tv", "type": "국영" },
      { "name": "Khabar TV", "domain": "khabar.kz", "type": "국영" }
    ],
    "newspapers": [
      { "name": "Egemen Kazakhstan", "domain": "egemen.kz", "type": "국영" },
      { "name": "Kazinform", "domain": "inform.kz", "type": "국영" }
    ]
  },
  "GE": {
    "name": "조지아",
    "broadcasting": [
      { "name": "Rustavi 2", "domain": "rustavi2.ge", "type": "민영" },
      { "name": "Imedi TV", "domain": "imedinews.ge", "type": "민영" }
    ],
    "newspapers": [
      { "name": "Agenda.ge", "domain": "agenda.ge", "type": "민영" },
      { "name": "Civil.ge", "domain": "civil.ge", "type": "민영" }
    ]
  }
}











async function uploadData() {
    const collectionRef = db.collection('media_credibility');
    console.log('Starting data upload to Firestore...');

    const promises = [];

    for (const [countryCode, data] of Object.entries(mediaData)) {
        const docRef = collectionRef.doc(countryCode);
        promises.push(docRef.set(data));
        console.log(`  - Preparing to upload data for ${countryCode} (${data.name})`);
    }

    try {
        await Promise.all(promises);
        console.log('\n✅ All media data successfully uploaded to Firestore collection "media_credibility".');
    } catch (error) {
        console.error('\n❌ Error uploading data to Firestore:', error);
    }
}

uploadData();
