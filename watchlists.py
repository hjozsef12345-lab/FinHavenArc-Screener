# 📋 WATCHLISTS BY COUNTRY CODE
# Enter your own tickers here (Yahoo base symbol, WITHOUT country code/suffix).
# The program automatically appends the appropriate Yahoo suffix (e.g. .T, .HK, etc.)
# E.g. for Toyota on the Tokyo exchange (7203.T): "T": ["7203"]
# ----------------------------------------------------------------------------------

japan_watchlist_by_suffix = {
    "T":  ["9984", "5802", "6723", "4568", "8802", "8801", "8830", "7532", "1812", "7012", "5334", "1803", "1942", "1944", "3288", "4182", "6269", "4403", "1959", "9412", "4536", "5631", "7003", "1893", "1980", "5741", "3350", "6407", "2264", "4368", "1332", "4666", "5857", "4043", "1417", "6814", "6744", "1979", "6703", "3186", "1861", "8986", "6516", "7906", "7220", "3498", "1377", "3569", "6996", "3433", "9793", "3445", "6588", "285A", "7011", "4519", "5803", "7936", "6361", "5706", "6976", "6323", "4751", "4980", "6871", "6834", "6590", "5384", "6544", "7552", "7744", "446A"],}   # Japan (Tokyo) 72 (35%)


south_korea_watchlist_by_suffix = {
    "KS": ["000100", "000270", "000660", "000720", "000990", "003230", "005850", "005930", "006260", "006280", "006800", "007340", "007660", "008770", "009150", "009420", "009540", "010060", "010130", "010140", "011070", "011210", "011780", "012330", "0126Z0", "028050", "028260", "031210", "032830", "035420", "035720", "036570", "047050", "052690", "064350", "064400", "068270", "071970", "082740", "086280", "103590", "111770", "112610", "207940", "241560", "251270", "259960", "267250", "267260", "267270", "271560", "278470", "281820", "282330", "298040", "307950", "322000", "326030", "329180", "352820", "353200", "383220", "402340", "439260", "454910", "483650", "489790"], # South Korea KS 67 (40%)
    "KQ": ["058610", "108490", "131970", "141080", "145020", "178320", "196170", "214150", "214450", "218410", "237690", "257720", "277810", "290650", "310210"],} # South Korea KQ 15 (40%)



australia_watchlist_by_suffix = {
    "AX": ["PLS", "XRO", "NXT", "APE", "SEK", "PDN", "WAF", "NIC", "PNI", "LTR", "ILU", "ALK", "RSG", "CIA", "CYL", "DVP", "FFM", "LYC", "HUB", "PDI", "NWL", "MSB", "PYC", "MI6", "NGI"],}   # Australia 25 (40%)


hongkong_watchlist_by_suffix = {
    "HK": ["0700", "1810", "2020", "9961", "0762", "0175", "1888", "2423", "0027", "9973", "6618", "2057", "1698", "6082", "0100", "0288", "9903", "1768", "1876", "6656", "2097", "0522", "2618", "0148", "0291", "2313", "0020", "0241", "2018", "1530", "9880", "0868", "7618", "3696", "0101", "1318", "3277", "2331", "1133", "2096", "0425", "1879", "0136", "0867", "3317", "0268", "2367", "3800", "0780", "6651", "2026", "3858", "0013", "2525", "1415", "2400", "9606", "0189", "0968", "2276", "2590", "1357", "0512", "9899", "1651", "2698", "6060", "9985", "0179", "3933", "2507", "6049", "1066", "3899", "6682", "2610", "2675", "3918", "0800", "1833", "1579", "1060", "9636", "2869", "1286", "0901", "2595", "0590", "2142", "1681", "0068", "1316", "1956", "1999", "1952", "2726", "0506", "9887", "6600", "6808", "1361", "6938", "2432", "1368", "2697", "6675", "2616", "1114", "0863", "2729", "1883", "2155", "1672", "3983", "3881", "0116", "0297", "0667", "1384", "9699", "1236", "2657", "6636", "2498", "0086", "1299", "0981", "3690", "1378", "1024", "1208", "1177", "3808", "1519", "9868", "1818", "9698", "9863", "6088", "2788", "0631", "1585", "9896", "0666", "9858", "1910", "2580", "1866", "3393", "1686", "0856", "1117", "3677", "2419", "2889"],} # Hong Kong 155 (35%)


taiwan_watchlist_by_suffix = {
"TW":["8210", "1476", "1590", "2337", "2344", "2345", "2368", "2383", "2472", "3036", "3376", "3596", "3661", "6415", "6515", "6531", "6781", "7750", "7769", "3090", "6139", "3583", "7799"], # Taiwan 23 (40%)
"TWO":["5289", "6584", "7734", "7828", "8069", "8358", "6274"],} # Taiwan 7 (40%)


china_watchlist_by_suffix = {
    # Shanghai Stock Exchange (SSE) - Yahoo suffix: .SS  (688xxx is the STAR Market)
    "SS": ["688256", "688041", "600276", "688235", "603986", "688808", "688008", "688802", "688795", "600176", "600031", "600584", "688120", "600522", "688183", "600160", "688271", "688702", "600118", "600415", "601179", "600066", "601231", "600426", "600378", "688019", "601808", "688629", "601117", "600985", "688375", "688336", "688220", "600570", "688775", "603806", "688300", "688322", "600030", "600309", "600989", "601066", "601995", "600346", "600010", "600875", "600089", "688249", "603799", "601788", "601901", "601233", "601877", "600096", "600498", "603659", "601058", "688223", "600995", "603260", "600392", "600143"],   # China - Shanghai (SSE, Stock Connect) 62 (40%) $5B+
    # Shenzhen Stock Exchange (SZSE) - Yahoo suffix: .SZ  (300xxx is the ChiNext)
    "SZ": ["300308", "300502", "002371", "002379", "300476", "002938", "300033", "300124", "001280", "000792", "002353", "000408", "002602", "301200", "002028", "301217", "002008", "002001", "300015", "002027", "002466", "002709", "300223", "001389", "000636", "300418", "300316", "002236", "000963", "002064", "002920", "300373", "002484", "002850", "002595", "002558", "002273", "000893", "002517", "300059", "000338", "000725", "000776", "300014", "000100", "000425", "002460", "000703", "002185", "002812", "301358", "002203", "000987", "300919", "002601"],}   # China - Shenzhen (SZSE, Stock Connect) 55 (40%) $5B+



germany_watchlist_by_suffix = {"DE": ["EVD", "TKMS", "OHB", "AMV0", "KRN", "FTK", "JUN3", "GBF", "VBK", "TNIE", "AOF", "VH2", "PFSE", "HEI", "SHA0", "ZAL", "TUI1", "FIE", "KTN", "VOS"],}  # Germany 20 (40%)
united_kingdom_watchlist_by_suffix = {"L": ["LSEG", "PRU", "RTO", "CNA", "MRO", "ICG", "IGG", "ROSE", "BPT", "INCH", "SRP", "MGNS", "SVS", "PFD", "RAT", "COA", "FGP", "CVSG", "STJ", "PAF", "HOC", "PLUS", "GNS", "YCA", "SAFE", "PTEC", "CORD", "CWR", "OCI", "MONY", "POLR", "PRN"],}   # United Kingdom 32 (30%)
france_watchlist_by_suffix = {"PA": ["MC", "EL", "SGO", "EN", "FGR", "TE", "ELIS", "VK", "MMB", "TRI", "IDL", "EMEIS", "ANTIN", "ABVX", "RF", "VU", "IPS", "VIV", "PEUG"],}   # France 19 (40%)
spain_watchlist_by_suffix = {"MC": ["CLNX", "GRF", "FDR", "CIE", "ENO", "VIS", "ALM", "SLR", "HBX", "ROVI", "PHM"],} # Spain 11 (30%)
italy_watchlist_by_suffix = {"MI": ["LDO", "DAN", "TGYM", "TIP", "FCT", "WBD"],}   # Italy 6 (40%)
belgium_watchlist_by_suffix = {"BR": ["UCB", "TUB"],} # Belgium 2 (40%)
netherlands_watchlist_by_suffix = {"AS": ["PRX", "HEIO", "BNJ", "AMG", "ADYEN", "HEIJM"],}   # Netherlands 6 (30%)
denmark_watchlist_by_suffix = {"CO": ["ALK-B", "DSV", "ZEAL"],} # Denmark 3 (40%)
sweden_watchlist_by_suffix = {"ST": ["BONEX", "EPRO-B", "VIT-B"],} # Sweden 3 (40%)
finland_watchlist_by_suffix = {"HE": ["IQMX"],}   # Finland 1 (40%)
norway_watchlist_by_suffix = {"OL": ["COSH","VEND"],} # Norway 2 (35%)
hungary_watchlist_by_suffix = {"BD": [],}   # Hungary
austria_watchlist_by_suffix = {"VI": ["PAL"],} # Austria 1 (40%)
switzerland_watchlist_by_suffix = {"SW": ["VACN", "ARYN", "SMG"],} # Switzerland 3 (40%)
turkey_watchlist_by_suffix = {"IS": ["ASELS", "ENKAI", "ASTOR", "TRALT", "TURSG", "OYAKC", "MGROS", "MPARK", "RGYAS", "TABGD", "TRMET", "GARAN", "AKBNK", "YKBNK", "FROTO", "CCOLA", "TOASO", "TAVHL", "AKSEN"],} # Turkey 19 (30%)
israel_watchlist_by_suffix = {"TA": ["MLSR", "NXSN", "SAE"],} # Israel 3 (40%)
greece_watchlist_by_suffix = {"AT": ["ELHA", "PPA", "AEGN"],} # Greece 3 (30%)
poland_watchlist_by_suffix = {"WA": ["KRU", "DOM"],} # Poland 2 (30%)



united_states_watchlist_by_suffix = {
        "USA": ["NVDA", "SPCX", "MU", "BABA", "WDC", "PDD", "KKR", "BN", "DASH", "INTU", "BSX", "COHR", "MSTR", "SE", "CRH", "RKLB", "LHX", "CBRS", "CRDO", "JBS", "UAL", "JD", "AXON", "RKT", "EQT", "BIDU", "RDDT", "TSEM", "GFS", "ECHO", "CPRT", "XYL", "FOX", "FWONA", "AMRZ", "CW", "RS", "STZ", "CRS", "FSLR", "CDE", "IP", "FIS", "DIDIY", "FN", "BMNR", "AS", "STRL", "ASND", "NBIX", "PFGC", "CG", "JLL", "YUMC", "SMMT", "ULS", "TRMB", "WY", "FLUT", "AMKR", "EQX", "GRAB", "ALB", "NXT", "TRU", "UHAL", "FIG", "AUR", "WSE", "AA", "VIAV", "DECK", "AES", "PINS", "SF", "KNX", "FNF", "RRX", "AR", "ALGN", "CHYM", "ONON", "DRS", "VSAT", "OC", "LTH", "APTV", "AAOI", "EDU", "YMM", "PNR", "PCVX", "SPXC", "SYRE", "KTOS", "VNOM", "ATR", "SFD", "AVAV", "RIOT", "SARO", "ESE", "POWL", "PRMB", "AAON", "COMP", "OKLO", "ALGM", "LAD", "BZ", "MGY", "TTAN", "MBLY", "DOX", "FAF", "BILI", "TEX", "Z", "ECG", "BLDR", "CRUS", "JOBY", "SGHC", "ACMR", "SYM", "COGT", "EPRT", "ORKA", "NAVN", "ORA", "NOVT", "BIRK", "AN", "KGS", "CRSP", "RYN", "AGX", "GXO", "BETA", "DFTX", "USAR", "ERAS", "MWH", "NXST", "AX", "HLNE", "DNTH", "KVYO", "KLAR", "MIDD", "MYRG", "UEC", "CRC", "FBIN", "VSEC", "RELY", "DIOD", "ATAT", "LPX", "TPC", "PSN", "GLXY", "ALK", "HRI", "VSNT", "MARA", "ONDS", "ESAB", "ENVA", "CECO", "RLAY", "AIR", "BC", "RDN", "FRVO", "TNGX", "PRIM", "TDS", "VKTX", "FLY", "JMKE", "ACHR", "XENE", "SITE", "ITRI", "LEGN", "BULL", "BOOT", "SLGN", "AMLX", "MAT", "OLED", "CENX", "MIR", "IPGP", "ELVN", "SRAD", "ACAD", "MIAX", "HNI", "MWA", "COCO", "CSTM", "DNLI", "LRN", "POST", "SMR", "RCUS", "FA", "LBRT", "DYN", "OUST", "DAN", "POWI", "BRZE", "NAMS", "KNF", "MMS", "KYIV", "CWK", "MBX", "NG", "BTDR", "FRPT", "CXT", "KC", "GPOR", "MZTI", "FUL", "REZI", "SOUN", "RDW", "HGV", "PRVA", "HAYW", "FRMI", "CALY", "CLDX", "BEAM", "HOS", "NESR", "IRON", "HIMX", "SUPN", "NRIX", "PURR", "VC", "BKV", "SLS", "AAP", "RSI", "NMRK", "LASR", "VERA", "ADMA", "OPEN", "ANDE", "UPST", "PHVS", "CALX", "RXRX", "PHIN", "PATK", "TRLV", "MLYS", "PBH", "GPCR", "CTOS", "DBD", "STUB", "STNE", "TRVI", "RUM", "ALGT", "VCEL", "RLX", "AADX", "SBET", "ETOR", "LCII", "PRDO", "SAH", "PVLA", "NLST", "TBBK", "VIR", "PENN", "DRVN", "BRVE", "NN", "UA", "QUBT", "STDN", "GENB", "BRSL", "BLBD", "ASTH", "OLN", "XRAY", "SHAZ", "NTLA", "HAPN", "STOK", "OCUL", "ANIP", "NKTR", "GLOB", "PAX", "RAPP", "ATEX"],}  # USA - no suffix needed 310 (40%)

   

united_states2_watchlist_by_suffix = {
    "USA": ["VNET", "TSHA", "GHRS", "OPRA", "TGLS", "OMCL", "STC", "KMPR", "MAZE", "INVA", "CASH", "USAS", "RVLV", "AVBP", "GENI", "TYRA", "KRP", "HAWK", "PGY", "AMPX", "COUR", "AMSC", "ARCO", "KRSA", "DMC", "VISN", "KLRA", "AGL", "SHLS", "KARD", "XNDU", "ARLO", "ORIC", "ATLC", "PSQL", "POET", "HLMN", "BBAI", "XZO", "EYE", "SLVM", "NSSC", "NMAX", "DMRA", "OMDA", "GOLD", "XPEL", "AVLN", "PRG", "LBRX", "BCAX", "VTOL", "CXM", "TBN", "YSS", "OPK", "HLIT", "AIP", "ROCK", "WLFC", "WLDN", "UMAC", "PUMP", "TPB", "MUX", "JCAP", "UTI", "AFYA", "ECVT", "AORT", "ODTX", "SPTX", "CRML", "DLX", "SVRA", "AKTS", "TUYA", "THRM", "JANX", "TRUP", "ITRN", "ANRO", "ANL", "GHM", "YELP", "GLUE", "FLOC", "CDNL", "EROK", "RGT"],}   # USA2 (because of the shared run with Europe, it can only start later, once Europe has closed)  90 (40%)



canada_watchlist_by_suffix = {
    "TO": ["AAUC", "ABRA", "AG", "AGI", "ARIS", "ATS", "BYD", "CADY", "CCO", "CIGI", "CNL", "EDR", "EFN", "GIL", "HMMC", "K", "MDA", "NGEX", "NXE", "OGC", "ONEX", "ORE", "PAAS", "PBH", "RBA", "SGD", "SVM", "TSU", "VNP", "WSP"],   # Canada TSX 30 (40%)
    "V":  ["AFM", "OMG", "PNG"],   # Canada TSX Venture 3 (40%)
    "CN": ["GTII"],                # Canada CSE 1 (40%)
}

mexico_watchlist_by_suffix = {
    "MX": ["BAFARB", "CHDRAUIB", "FEXI21", "FRAGUAB", "GCC", "GENTERA", "GRUMAB", "KUOA", "VISTAA"],}   # Mexico (separate market: in summer the Mexican exchange closes 1 hour later than the US) 9 (40%)


brazil_watchlist_by_suffix = {"SA": ["LREN3", "ALPA3", "BRAP3", "MDIA3", "SUZB3", "RENT3", "MBRF3", "CSMG3", "PASS3", "SMFT3", "ORVR3", "GGPS3", "SIMH3", "DIRR3", "TTEN3", "POMO3"]}   # Brazil 16 (30%)
