# -*- coding: utf-8 -*-
"""Generate ref.bib + refmap.tsv from the reference list of 论文起草.md.

Source of truth for the *text* is D:\\GYH\\coding\\git\\immc-2027\\正稿\\论文起草v2\\论文起草.md
(lines 872-1020).  Field values below are transcribed from those lines; markdown
escapes (\\. \\- \\( \\) \\& \\_ \\* \\[ \\]) are undone, LaTeX-unsafe characters in
text fields are re-escaped by hand (& -> \\&, _ -> \\_ inside prose).
URL/DOI fields are emitted verbatim (biblatex typesets them with \\url).
"""
import io, os, re, sys

SRC = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v2\论文起草.md"
OUT = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex"

# (key, entrytype, namespace, original marker, source line, [(field, value), ...])
E = [
# ---------------------------------------------------------------- 第一问, seq 1
("q1ref01", "techreport", "第一问", "1", 876, [
    ("author", "{{International Telecommunication Union}}"),
    ("title", "Best practices for green data centres"),
    ("institution", "International Telecommunication Union"),
    ("type", "Recommendation"),
    ("number", "ITU-T L.1300"),
    ("year", "2014"),
    ("note", "\u00a712.1"),
    ("url", "https://www.itu.int/rec/T-REC-L.1300-201406-I/en"),
]),
("q1ref02", "article", "第一问", "2", 878, [
    ("author", "Jones, E. R. and others"),
    ("title", "A multi-model assessment of global freshwater temperature and thermoelectric power supply under climate change"),
    ("journaltitle", "Environmental Research: Water"),
    ("year", "2025"),
    ("volume", "1"),
    ("pages", "025002"),
    ("doi", "10.1088/3033-4942/addffa"),
]),
("q1ref03", "article", "第一问", "3", 880, [
    ("author", "Parzen, M. and others"),
    ("title", "PyPSA-Earth. A new global open energy system optimization model demonstrated in Africa"),
    ("journaltitle", "Applied Energy"),
    ("year", "2023"),
    ("volume", "341"),
    ("pages", "121096"),
    ("doi", "10.1016/j.apenergy.2023.121096"),
]),
("q1ref04", "inproceedings", "第一问", "4", 882, [
    ("author", "Goiri, I. and others"),
    ("title", "Parasol and GreenSwitch: Managing datacenters powered by renewable energy"),
    ("booktitle", "Proceedings of ASPLOS"),
    ("year", "2013"),
    ("doi", "10.1145/2451116.2451123"),
]),
("q1ref05", "article", "第一问", "5", 884, [
    ("author", "Macknick, J. and Newmark, R. and Heath, G. and Hallett, K. C."),
    ("title", "Operational water consumption and withdrawal factors for electricity generating technologies: A review of existing literature"),
    ("journaltitle", "Environmental Research Letters"),
    ("year", "2012"),
    ("volume", "7"),
    ("pages", "045802"),
    ("doi", "10.1088/1748-9326/7/4/045802"),
]),
("q1ref06", "techreport", "第一问", "6", 886, [
    ("author", "{{EG\\&G Idaho, Inc.}}"),
    ("title", "Microhydropower Handbook, Volume 2"),
    ("institution", "U.S. Department of Energy"),
    ("year", "1983"),
    ("number", "IDO-10107"),
    ("note", "引用位置：Appendix A-1, \\emph{Development of the Power Equation}, p.~A1-1"),
    ("url", "https://www.energy.gov/sites/default/files/2019/01/f59/Microhydropower_Handbook_2.pdf"),
]),
# ---------------------------------------------------------------- 第一问, seq 2
("q1bref01", "techreport", "第一问", "1", 892, [
    ("author", "Kuzma, S. and others"),
    ("title", "Aqueduct 4.0: Updated Decision-Relevant Global Water Risk Indicators"),
    ("institution", "World Resources Institute"),
    ("year", "2023"),
    ("doi", "10.46830/writn.23.00061"),
]),
("q1bref02", "article", "第一问", "2", 894, [
    ("author", "Hoekstra, A. Y. and others"),
    ("title", "Global monthly water scarcity: Blue water footprints versus blue water availability"),
    ("journaltitle", "PLOS ONE"),
    ("year", "2012"),
    ("volume", "7"),
    ("number", "2"),
    ("pages", "e32688"),
    ("doi", "10.1371/journal.pone.0032688"),
]),
("q1bref03", "article", "第一问", "3", 896, [
    ("author", "Pastor, A. V. and others"),
    ("title", "Accounting for environmental flow requirements in global water assessments"),
    ("journaltitle", "Hydrology and Earth System Sciences"),
    ("year", "2014"),
    ("volume", "18"),
    ("pages", "5041--5059"),
    ("doi", "10.5194/hess-18-5041-2014"),
]),
("q1bref04", "article", "第一问", "4", 898, [
    ("author", "Mytton, D."),
    ("title", "Data centre water consumption"),
    ("journaltitle", "npj Clean Water"),
    ("year", "2021"),
    ("volume", "4"),
    ("pages", "11"),
    ("doi", "10.1038/s41545-021-00101-w"),
]),
("q1bref05", "techreport", "第一问", "5", 900, [
    ("author", "Sickinger, D. E. and others"),
    ("title", "Thermosyphon Cooler Hybrid System for Water Savings in an Energy-Efficient HPC Data Center: Results from 24 Months and the Impact on Water Usage Effectiveness"),
    ("institution", "National Renewable Energy Laboratory"),
    ("year", "2018"),
    ("doi", "10.2172/1471661"),
]),
("q1bref06", "article", "第一问", "6", 902, [
    ("author", "Wurbs, R. A."),
    ("title", "Texas Water Availability Modeling System"),
    ("journaltitle", "Journal of Water Resources Planning and Management"),
    ("year", "2005"),
    ("volume", "131"),
    ("number", "4"),
    ("pages", "270--279"),
    ("doi", "10.1061/%28ASCE%290733-9496%282005%29131%3A4%28270%29"),
]),
("q1bref07", "article", "第一问", "7", 904, [
    ("author", "Okeola, O. G. and Balogun, S. O."),
    ("title", "Estimating a municipal water supply reliability"),
    ("journaltitle", "Cogent Engineering"),
    ("year", "2015"),
    ("volume", "2"),
    ("number", "1"),
    ("pages", "1012988"),
    ("doi", "10.1080/23311916.2015.1012988"),
]),
("q1bref08", "techreport", "第一问", "8", 906, [
    ("author", "Dieter, C. A. and others"),
    ("title", "Estimated use of water in the United States in 2015"),
    ("institution", "U.S. Geological Survey"),
    ("type", "Circular"),
    ("number", "1441"),
    ("year", "2018"),
    ("doi", "10.3133/cir1441"),
]),
("q1bref09", "article", "第一问", "9", 908, [
    ("author", "SIDDIK M A B and SHEHABI A and MARSTON L"),
    ("title", "The environmental footprint of data centers in the United States"),
    ("journaltitle", "Environmental Research Letters"),
    ("year", "2021"),
    ("volume", "16"),
    ("number", "6"),
    ("pages", "064017"),
    ("doi", "10.1088/1748-9326/abfba1"),
]),
("q1bref10", "online", "第一问", "10", 910, [
    ("author", "{{Colorado\u2019s Decision Support Systems (CDSS)}}"),
    ("title", "StateMod"),
    ("url", "https://cdss.colorado.gov/software/statemod"),
    ("urldate", "2026-11-22"),
]),
# ---------------------------------------------------------------- 附录 [4-n]
("apxref01", "online", "附录", "4-1", 914, [
    ("author", "{{Crusoe}}"),
    ("title", "An inside look at the Abilene AI data center"),
    ("url", "https://www.crusoe.ai/resources/blog/an-inside-look-at-the-abilene-ai-data-center"),
]),
("apxref02", "online", "附录", "4-2", 916, [
    ("author", "{{Crusoe}}"),
    ("title", "Crusoe expands AI data center campus in Abilene to 1.2 gigawatts"),
    ("url", "https://www.crusoe.ai/resources/newsroom/crusoe-expands-ai-data-center-campus-in-abilene-to-1-2-gigawatts"),
]),
("apxref03", "online", "附录", "4-3", 918, [
    ("author", "{{DPR Construction}}"),
    ("title", "Crusoe Abilene data center"),
    ("url", "https://www.dpr.com/projects/crusoe-abilene-data-center"),
]),
("apxref04", "online", "附录", "4-4", 920, [
    ("author", "{{Oracle}}"),
    ("title", "Abilene data center"),
    ("url", "https://www.oracle.com/data-centers/abilene/"),
]),
("apxref05", "misc", "附录", "4-5", 922, [
    ("author", "{{IMMC 2027 组委会}}"),
    ("title", "Problem A: How big an AI data center to be?"),
    ("year", "2026"),
    ("note", "第 1--2、5--6 页"),
]),
("apxref06", "article", "附录", "4-6", 924, [
    ("author", "Macknick, J. and Newmark, R. and Heath, G. and Hallett, K. C."),
    ("title", "Operational water consumption and withdrawal factors for electricity generating technologies: A review of existing literature"),
    ("journaltitle", "Environmental Research Letters"),
    ("year", "2012"),
    ("volume", "7"),
    ("pages", "045802"),
    ("doi", "10.1088/1748-9326/7/4/045802"),
    ("note", "与 q1ref05 为同一条文献，正文按 [4-6] 引用"),
]),
("apxref07", "techreport", "附录", "4-7", 926, [
    ("author", "Ong, S. and Campbell, C. and Denholm, P. and Margolis, R. and Heath, G."),
    ("title", "Land-use requirements for solar power plants in the United States"),
    ("institution", "National Renewable Energy Laboratory"),
    ("number", "NREL/TP-6A20-56290"),
    ("year", "2013"),
    ("doi", "10.2172/1086349"),
]),
("apxref08", "online", "附录", "4-8", 928, [
    ("author", "{{Epoch AI}}"),
    ("title", "AI data centers"),
    ("url", "https://epoch.ai/data/ai-data-centers"),
    ("note", "分项容量：\\url{https://epoch.ai/graphs/largest-ai-data-centers-by-power-capacity}"),
]),
("apxref09", "techreport", "附录", "4-9", 930, [
    ("author", "{{Texas Water Development Board}}"),
    ("title", "2026 Region G regional water plan, Volume I"),
    ("institution", "Texas Water Development Board"),
    ("year", "2026"),
    ("note", "原文页码 607"),
    ("url", "https://www.twdb.texas.gov/waterplanning/rwp/plans/2026/G/RegionG_2026_RWP_VolumeI.pdf"),
]),
("apxref10", "online", "附录", "4-10", 932, [
    ("author", "{{Open-Meteo}}"),
    ("title", "Historical weather API (ERA5)"),
    ("url", "https://open-meteo.com/en/docs/historical-weather-api"),
]),
("apxref11", "misc", "附录", "4-11", 934, [
    ("author", "{{City of Abilene}}"),
    ("title", "Lancium LLC Abilene second amended and restated tax abatement agreement"),
    ("year", "2025"),
    ("note", "原文页码 25"),
    ("url", "https://abilenetx.gov/DocumentCenter/View/39456/Lancium-LLC-Abilene-Second-Amended-and-Restated-Tax-Abatement-Agreement-PDF"),
]),
("apxref12", "misc", "附录", "4-12", 936, [
    ("author", "{{City of Abilene}}"),
    ("title", "SP-2026-77 (specific use permit)"),
    ("year", "2026"),
    ("url", "https://abilenetx.gov/DocumentCenter/View/43833/SP-2026-77-PDF"),
]),
("apxref13", "online", "附录", "4-13", 938, [
    ("author", "{{Mortenson}}"),
    ("title", "Abilene data center development"),
    ("url", "https://www.mortenson.com/projects/abilene-data-center-development"),
]),
("apxref14", "techreport", "附录", "4-14", 940, [
    ("author", "Denholm, P. and Hand, M. and Jackson, M. and Ong, S."),
    ("title", "Land-use requirements of modern wind power plants in the United States"),
    ("institution", "National Renewable Energy Laboratory"),
    ("number", "NREL/TP-6A2-45834"),
    ("year", "2009"),
    ("doi", "10.2172/964608"),
]),
("apxref15", "techreport", "附录", "4-15", 942, [
    ("author", "Kuzma, S. and Bierkens, M. F. P. and Lakshman, S. and others"),
    ("title", "Aqueduct 4.0: updated decision-relevant global water risk indicators"),
    ("institution", "World Resources Institute"),
    ("year", "2023"),
    ("doi", "10.46830/writn.23.00061"),
]),
("apxref16", "misc", "附录", "4-16", 944, [
    ("author", "{{Verne}}"),
    ("title", "Iceland data sheet"),
    ("year", "2025"),
    ("url", "https://www.verneglobal.com/hubfs/Downloadable_Content/Datasheets%202025/Iceland_Datasheet%20.pdf"),
]),
("apxref17", "online", "附录", "4-17", 946, [
    ("author", "{{Verne}}"),
    ("title", "Launch of a high-capacity substation in Keflav\u00edk"),
    ("year", "2026"),
    ("url", "https://www.verne.co/news/news-verne-and-landsnet-launch-high-capacity-substation"),
]),
("apxref18", "misc", "附录", "4-18", 948, [
    ("author", "{{Skipulagsstofnun (UUA)}}"),
    ("title", "Uppbygging gagnavers"),
    ("year", "2026"),
    ("url", "https://uua.is/urleits/uua2606003-uppbygging-gagnavers/"),
]),
("apxref19", "online", "附录", "4-19", 950, [
    ("author", "{{Meta}}"),
    ("title", "Rethinking data center design for Singapore"),
    ("year", "2019"),
    ("url", "https://datacenters.atmeta.com/2019/01/rethinking-data-center-design-for-singapore/"),
]),
("apxref20", "online", "附录", "4-20", 952, [
    ("author", "{{PUB, Singapore}}"),
    ("title", "Sectoral water efficiency benchmark"),
    ("url", "https://www.pub.gov.sg/public/waterloop/water-conservation/resources-on-water-efficiency-measures/sectoral-water-efficiency-benchmark"),
]),
("apxref21", "techreport", "附录", "4-21", 954, [
    ("author", "{{Monetary Authority of Singapore}}"),
    ("title", "Singapore-Asia taxonomy for sustainable finance"),
    ("institution", "Monetary Authority of Singapore"),
    ("year", "2023"),
    ("url", "https://www.mas.gov.sg/-/media/mas-media-library/development/sustainable-finance/singaporeasia-taxonomy-updated.pdf"),
]),
("apxref22", "misc", "附录", "4-22", 956, [
    ("author", "{{Servicio de Evaluaci\u00f3n Ambiental (SEA), Chile}}"),
    ("title", "Documento ambiental del proyecto de centro de datos en Quilicura"),
    ("year", "2022"),
    ("url", "https://infofirma.sea.gob.cl/DocumentosSEA/MostrarDocumento?docId=56%2F79%2F5da3b81f2f6e96f0e1740ab072571d17e39a"),
]),
("apxref23", "online", "附录", "4-23", 958, [
    ("author", "{{Google}}"),
    ("title", "10 datos sobre el centro de datos de Google en Quilicura, Chile"),
    ("url", "https://blog.google/intl/es-419/noticias-de-la-empresa/10-datos-sobre-el-centro-de-datos-de-google-en-quilicura-chile/"),
]),
("apxref24", "misc", "附录", "4-24", 960, [
    ("author", "{{Coordinador El\u00e9ctrico Nacional, Chile}}"),
    ("title", "Minuta: solicitud nueva subestaci\u00f3n Colina"),
    ("year", "2021"),
    ("url", "https://www.coordinador.cl/wp-content/uploads/2021/08/Minuta_Solicitud_Nueva_Subestacion_COLINA_24_08_2021.pdf"),
]),
("apxref25", "online", "附录", "4-25", 962, [
    ("author", "{{AirTrunk}}"),
    ("title", "AirTrunk expands western Sydney region with new SYD3 hyperscale data centre"),
    ("year", "2023"),
    ("url", "https://airtrunk.com/airtrunk-expands-western-sydney-region-with-new-syd3-hyperscale-data-centre-asia-pacifics-largest/"),
]),
("apxref26", "online", "附录", "4-26", 964, [
    ("author", "{{NSW Department of Planning}}"),
    ("title", "51 Huntingwood Drive data centre (SSD-41589232)"),
    ("url", "https://www.planningportal.nsw.gov.au/major-projects/projects/51-huntingwood-drive-data-centre"),
]),
("apxref27", "misc", "附录", "4-27", 966, [
    ("author", "{{NSW Department of Planning}}"),
    ("title", "SSD-41589232: water supply assessment"),
    ("year", "2022"),
    ("url", "https://majorprojects.planningportal.nsw.gov.au/prweb/PRRestService/mp/01/getContent?AttachRef=SSD-41589232%2120220916T041049.122+GMT"),
]),
("apxref28", "misc", "附录", "4-28", 968, [
    ("author", "{{NPS}}"),
    ("title", "NPS-100C small wind turbine brochure"),
    ("year", "2019"),
    ("url", "https://www.nps100.com/wp/wp-content/uploads/2022/10/brochure-NPS-100C-24_ed2019_light_ENG.pdf"),
]),
("apxref29", "online", "附录", "4-29", 970, [
    ("author", "{{OpenAI}}"),
    ("title", "Codex CLI（开源编码代理工具）"),
    ("year", "2026"),
    ("url", "https://github.com/openai/codex"),
]),
# ---------------------------------------------------------------- 第二问
("q2ref01", "misc", "第二问", "1", 978, [
    ("title", "UNU-INWEH-Report-The\\_Env\\_Cost\\_of\\_AI-2026"),
    ("note", "原始条目仅给出 URL，未给出作者与题名；标题按文件名转写"),
    ("url", "https://unu.edu/sites/default/files/2026-10/UNU-INWEH-Report-The_Env_Cost_of_AI-2026.pdf"),
]),
("q2bref01", "online", "第二问", "1", 982, [
    ("author", "{{生态环境部 and 国家统计局}}"),
    ("title", "关于发布2023年电力二氧化碳排放因子的公告：公告2025年第47号"),
    ("date", "2025-12-31"),
    ("url", "https://www.mee.gov.cn/xxgk2018/xxgk/xxgk01/202512/t20251231_1139517.html"),
    ("note", "附件：\\url{https://www.mee.gov.cn/xxgk2018/xxgk/xxgk01/202512/W020251231726284332528.pdf}"),
]),
("q2bref02", "online", "第二问", "2", 988, [
    ("author", "{{生态环境部}}"),
    ("title", "生态环境部应对气候变化司有关负责人就《关于发布2023年电力二氧化碳排放因子的公告》答记者问"),
    ("date", "2026-01-05"),
    ("url", "https://www.mee.gov.cn/ywdt/zbft/202601/t20260105_1139911.shtml"),
]),
("q2cref01", "online", "第二问", "1", 994, [
    ("author", "{{SETI@home}}"),
    ("title", "SETI@home"),
    ("note", "原始条目仅给出 URL；题名取自站点域名"),
    ("url", "https://setiathome.berkeley.edu/sah_about.php"),
]),
("q2cref02", "misc", "第二问", "1", 996, [
    ("doi", "10.1109/JLT.2014.2301450"),
    ("note", "原始条目仅给出 DOI，未给出作者、题名与年份"),
]),
("q2cref03", "misc", "第二问", "2", 998, [
    ("doi", "10.1016/j.dcan.2025.11.006"),
    ("note", "原始条目仅给出 DOI，未给出作者、题名与年份"),
]),
# ---------------------------------------------------------------- 附录 [L1-L5]
("apxrefL01", "article", "附录", "L1", 1002, [
    ("author", "Wu, G. C. and Torn, M. S. and Williams, J. H."),
    ("title", "Incorporating land-use requirements and environmental constraints in low-carbon electricity planning for California"),
    ("journaltitle", "Environmental Science \\& Technology"),
    ("year", "2015"),
    ("volume", "49"),
    ("number", "4"),
    ("pages", "2013--2021"),
    ("doi", "10.1021/es502979v"),
]),
("apxrefL02", "misc", "附录", "L2", 1006, [
    ("author", "{{Epoch AI}}"),
    ("title", "AI Data Centers"),
    ("note", "[dataset] 数据库与来源说明：\\url{https://epoch.ai/data/ai-data-centers}"),
    ("url", "https://epoch.ai/data/ai-data-centers"),
]),
("apxrefL03", "article", "附录", "L3", 1010, [
    ("author", "Lovering, J. and Swain, M. and Blomqvist, L. and Hernandez, R. R."),
    ("title", "Land-use intensity of electricity production and tomorrow\u2019s energy landscape"),
    ("journaltitle", "PLOS ONE"),
    ("year", "2022"),
    ("volume", "17"),
    ("number", "7"),
    ("pages", "e0270155"),
    ("doi", "10.1371/journal.pone.0270155"),
]),
("apxrefL04", "techreport", "附录", "L4", 1014, [
    ("author", "Ong, S. and Campbell, C. and Denholm, P. and Margolis, R. and Heath, G."),
    ("title", "Land-Use Requirements for Solar Power Plants in the United States"),
    ("institution", "National Renewable Energy Laboratory"),
    ("number", "NREL/TP-6A20-56290"),
    ("year", "2013"),
    ("doi", "10.2172/1086349"),
]),
("apxrefL05", "techreport", "附录", "L5", 1018, [
    ("author", "Denholm, P. and Hand, M. and Jackson, M. and Ong, S."),
    ("title", "Land-Use Requirements of Modern Wind Power Plants in the United States"),
    ("institution", "National Renewable Energy Laboratory"),
    ("number", "NREL/TP-6A2-45834"),
    ("year", "2009"),
    ("doi", "10.2172/964608"),
]),
]

BIB_HEADER = """% ref.bib -- bibliography for the biblatex (style=ieee) build.
% Transcribed from 正稿/论文起草v2/论文起草.md, lines 872-1020 (section "# 参考文献").
% Citekey scheme (see refmap.tsv):
%   q1refNN   第一问, reference list lines 876-886  ([1]-[6])
%   q1brefNN  第一问, reference list lines 892-910 ([1]-[10], numbering restarts)
%   apxrefNN  附录 / [4-N] block, lines 914-970    (original 4-N -> apxrefNN)
%   q2refNN   第二问, line 978
%   q2brefNN  第二问 "碳足迹参考文献", lines 982/988 (numbering restarts)
%   q2crefNN  第二问 "集中式数据设施", lines 994-998 (numbering restarts twice)
%   apxrefLNN 附录 [L1]-[L5], lines 1002-1018
% URL and DOI fields are verbatim (biblatex typesets them with \\url); all other
% fields are LaTeX-escaped. UTF-8, no BOM.
"""


def bib_entry(key, typ, fields):
    lines = ["@%s{%s," % (typ, key)]
    for i, (name, val) in enumerate(fields):
        comma = "," if i < len(fields) - 1 else ""
        lines.append("  %-14s = {%s}%s" % (name, val, comma))
    lines.append("}")
    return "\n".join(lines)


def unescape_md(s):
    s = re.sub(r"\\([.\-()&_*\[\]{}#$%+])", r"\1", s)
    s = s.replace("\\", "")
    return s


def ref_text(line):
    t = line
    t = re.sub(r"^\\\[[^\]]*\\\]", "", t)     # \[1\] / \[4-1\] / \[L1\]
    t = re.sub(r"^［[^］]*］", "", t)           # ［1］
    t = re.sub(r"\*\*", "", t)
    t = unescape_md(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def main():
    os.makedirs(OUT, exist_ok=True)
    with io.open(SRC, encoding="utf-8") as f:
        src = f.read().splitlines()

    keys = set()
    for key, _t, _ns, _m, _ln, _f in E:
        assert key not in keys, "duplicate key %s" % key
        keys.add(key)

    parts = [BIB_HEADER]
    for key, typ, ns, marker, line, fields in E:
        names = [n for n, _ in fields]
        assert len(names) == len(set(names)), "dup field in %s" % key
        assert "title" in names or "note" in names, key
        parts.append("\n" + bib_entry(key, typ, fields))
    bib = "\n".join(parts) + "\n"
    with io.open(os.path.join(OUT, "ref.bib"), "w", encoding="utf-8", newline="\n") as f:
        f.write(bib)

    rows = []
    for key, typ, ns, marker, line, fields in E:
        txt = ref_text(src[line - 1])
        rows.append("%s\t%s\t%s\t%s" % (ns, marker, key, txt[:60]))
    with io.open(os.path.join(OUT, "refmap.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(rows) + "\n")

    # ---- validation
    depth = 0
    for i, ch in enumerate(bib):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            assert depth >= 0, "unbalanced } at %d" % i
    assert depth == 0, "braces unbalanced by %d" % depth
    n_entries = bib.count("\n@")
    print("entries:", len(E), "(@ counts:", n_entries + 1, ")")
    print("brace balance: OK")
    from collections import Counter
    print("per namespace:", Counter(ns for _k, _t, ns, _m, _l, _f in E))
    print("types:", Counter(t for _k, t, _n, _m, _l, _f in E))
    print("refmap rows:", len(rows))


if __name__ == "__main__":
    main()
