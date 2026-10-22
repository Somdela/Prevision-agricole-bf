"""
Anticiper la campagne agricole au Burkina Faso
Plateforme de démonstration · Romba Abdoul Aziz · École Mohammadia d'Ingénieurs

L'application ne calcule rien : elle lit les fichiers produits dans Colab (étapes 8 à 12)
et les met en forme. Pour mettre à jour un résultat, on remplace le fichier CSV correspondant.
"""
import json
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Campagne agricole · Burkina Faso", page_icon=":material/grass:",
                   layout="wide", initial_sidebar_state="collapsed")

ICI = Path(__file__).parent
# Les CSV peuvent être dans un dossier data/ ou directement à côté de app.py
DATA = ICI / "data" if (ICI / "data").is_dir() else ICI

# ------------------------------------------------------------------ identité visuelle
# Indigo du Faso Dan Fani, or du mil, vert de l'hivernage, rouge de la latérite
INDIGO, MIL, HIVERNAGE, LATERITE = "#1F2A44", "#D9A21B", "#2E7D5B", "#B4442C"
FOND, BRUME, ENCRE_DOUCE, NEUTRE = "#F4F6F5", "#E3E8E5", "#5B6475", "#EEF0EC"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Public+Sans:wght@400;500;600;700&display=swap');
html, body, .stApp, .stMarkdown, button, input, textarea, select {{ font-family: 'Public Sans', sans-serif; }}
.stApp {{ background: {FOND}; color: {INDIGO}; }}
.block-container {{ max-width: 1180px; padding-top: 4.6rem; padding-bottom: 4rem; }}
h1, h2, h3, h4 {{ font-family: 'Bricolage Grotesque', sans-serif !important; color: {INDIGO}; letter-spacing: -0.015em; }}
h1 {{ font-weight: 800 !important; font-size: 2.7rem !important; line-height: 1.04 !important; }}
h2 {{ font-weight: 700 !important; font-size: 1.7rem !important; margin-top: 1.6rem !important; }}
h3 {{ font-weight: 700 !important; font-size: 1.2rem !important; }}
[data-testid="stHeaderActionElements"], [data-testid="stSidebarCollapsedControl"], footer {{ display: none !important; }}
p, li {{ line-height: 1.6; }}
.stMarkdown p {{ max-width: 72ch; }}
.chiffre {{ font-variant-numeric: tabular-nums; }}

/* ruban tissé, inspiré des bandes du Faso Dan Fani */
.ruban {{ display: block; height: 10px; font-size: 0; line-height: 0; border-radius: 3px; margin: 0 0 1.4rem 0;
  background: repeating-linear-gradient(90deg, {INDIGO} 0 22px, {MIL} 22px 27px, {FOND} 27px 29px,
  {HIVERNAGE} 29px 41px, {FOND} 41px 43px, {LATERITE} 43px 48px, {INDIGO} 48px 56px); }}

/* bandeau d'accueil */
.st-key-hero {{ background: {INDIGO}; border-radius: 22px; padding: 2.2rem 2.2rem 1.4rem 2.4rem; }}
.st-key-hero h1, .st-key-hero p, .st-key-hero li, .st-key-hero span {{ color: #FFFFFF !important; }}
.st-key-hero .sous {{ color: #C9D1E3 !important; font-size: 1.08rem; max-width: 46ch; }}
.st-key-hero .constat {{ font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.45rem; font-weight: 700;
  line-height: 1.25; color: {MIL} !important; margin: 1.4rem 0 0.4rem 0; max-width: 24ch; }}
.st-key-hero .legende {{ color: #AEB8CF !important; font-size: 0.9rem; }}

/* réponses : un filet de couleur dit si la nouvelle est bonne, mauvaise ou neutre */
.reponse {{ background: #FFFFFF; border-left: 5px solid {BRUME}; border-radius: 4px 14px 14px 4px;
  padding: 1.1rem 1.3rem 0.9rem 1.3rem; height: 100%; }}
.reponse.bonne {{ border-left-color: {HIVERNAGE}; }}
.reponse.mauvaise {{ border-left-color: {LATERITE}; }}
.reponse.neutre {{ border-left-color: {MIL}; }}
.reponse .question {{ color: {ENCRE_DOUCE}; font-size: 0.95rem; margin: 0; }}
.reponse .reponse-texte {{ font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.25rem; font-weight: 700;
  line-height: 1.25; margin: 0.35rem 0 0.4rem 0; color: {INDIGO}; }}
.reponse .detail {{ color: {ENCRE_DOUCE}; font-size: 0.9rem; margin: 0; }}

/* fiche de prévision des prix */
.ticket {{ background: #FFFFFF; border-radius: 16px; padding: 1.2rem 1.3rem; }}
.ticket .ligne {{ display: grid; grid-template-columns: 1fr auto; gap: 0.2rem 1rem; padding: 0.7rem 0;
  border-bottom: 1px solid {BRUME}; }}
.ticket .ligne:last-child {{ border-bottom: none; }}
.ticket .quand {{ color: {ENCRE_DOUCE}; font-size: 0.9rem; }}
.ticket .prix {{ font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 1.5rem;
  font-variant-numeric: tabular-nums; text-align: right; }}
.ticket .fourchette {{ color: {ENCRE_DOUCE}; font-size: 0.85rem; grid-column: 1 / 3; }}
.ticket .hausse {{ color: {LATERITE}; font-weight: 600; }}
.ticket .baisse {{ color: {HIVERNAGE}; font-weight: 600; }}

.note {{ color: {ENCRE_DOUCE}; font-size: 0.88rem; }}
.pied {{ color: {ENCRE_DOUCE}; font-size: 0.85rem; border-top: 1px solid {BRUME}; margin-top: 3rem; padding-top: 1rem; }}
[data-testid="stExpander"] {{ background: #FFFFFF; border-radius: 12px; border: none; }}
[data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; }}
</style>
""", unsafe_allow_html=True)


def theme_altair():
    return {"config": {
        "font": "Public Sans, Helvetica Neue, Arial, sans-serif",
        "background": "transparent",
        "view": {"stroke": None},
        "axis": {"labelColor": ENCRE_DOUCE, "titleColor": ENCRE_DOUCE, "gridColor": BRUME, "domain": False,
                 "tickColor": BRUME, "labelFontSize": 12, "titleFontSize": 12, "titleFontWeight": 500},
        "legend": {"labelColor": INDIGO, "titleColor": ENCRE_DOUCE, "labelFontSize": 12, "orient": "bottom"},
        "header": {"labelFont": "Bricolage Grotesque, Helvetica Neue, Arial, sans-serif", "labelFontSize": 15, "labelColor": INDIGO},
        "title": {"font": "Bricolage Grotesque, Helvetica Neue, Arial, sans-serif", "color": INDIGO, "fontSize": 15, "anchor": "start"},
    }}


try:                                   # Altair 5.5 et plus
    alt.theme.register("faso", enable=True)(theme_altair)
except AttributeError:                 # versions plus anciennes
    alt.themes.register("faso", theme_altair)
    alt.themes.enable("faso")

CEREALES = ["maïs", "mil", "sorgho", "riz"]
DATES_DECISION = {18: "fin juin", 19: "10 juillet", 20: "20 juillet", 21: "fin juillet",
                  22: "10 août", 23: "20 août", 24: "fin août"}
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]


# ------------------------------------------------------------------ données
@st.cache_data
def lire(nom, dates=()):
    return pd.read_csv(DATA / nom, parse_dates=list(dates))


@st.cache_data
def provinces():
    p = lire("provinces.csv")
    p["nom"] = np.where(p["changement"] == "inchangée", p["province_2025"],
                        p["province_2025"] + " (ex-" + p["province_ancienne"] + ")")
    return p.set_index("fnid")


@st.cache_data
def contours():
    return json.loads((DATA / "provinces.geojson").read_text(encoding="utf-8"))["features"]


PROV = provinces()


def nom_province(fnid):
    return PROV["nom"].get(fnid, fnid)


def fr(x, d=0):
    """Nombre à la française : virgule décimale, espace pour les milliers."""
    s = f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
    return s


def signe(x, d=0):
    return ("+" if x > 0 else "−" if x < 0 else "") + fr(abs(x), d)


def mois_fr(d):
    return f"{MOIS[d.month - 1]} {d.year}"


def carte(df, valeur, titre, echelle, format_valeur=".0f", unite="", hauteur=430, contour_col=None):
    """Carte des 45 provinces, colorée par la colonne `valeur` de df (indexé par fnid)."""
    d = df.reset_index()[["fnid", valeur] + ([contour_col] if contour_col else [])].copy()
    d["nom"] = d["fnid"].map(nom_province)
    champs = [valeur, "nom"] + ([contour_col] if contour_col else [])
    fond = alt.Chart(alt.Data(values=contours())).mark_geoshape(fill=BRUME, stroke="#FFFFFF", strokeWidth=0.8)
    couche = alt.Chart(alt.Data(values=contours())).mark_geoshape(stroke="#FFFFFF", strokeWidth=0.8).transform_lookup(
        lookup="properties.fnid", from_=alt.LookupData(d, "fnid", champs)
    ).encode(
        color=alt.Color(f"{valeur}:Q", scale=echelle, title=titre,
                        legend=alt.Legend(orient="bottom", gradientLength=260, format=format_valeur, titleLimit=500)),
        tooltip=[alt.Tooltip("nom:N", title="province"), alt.Tooltip(f"{valeur}:Q", title=titre, format=format_valeur)],
    ).transform_filter(f"isValid(datum['{valeur}'])")
    couches = [fond, couche]
    if contour_col:
        couches.append(alt.Chart(alt.Data(values=contours())).mark_geoshape(
            fill=None, stroke=INDIGO, strokeWidth=2.2).transform_lookup(
            lookup="properties.fnid", from_=alt.LookupData(d, "fnid", [contour_col])
        ).transform_filter(f"datum['{contour_col}'] == 1"))
    return alt.layer(*couches).project(type="mercator").properties(height=hauteur)


def divergente(borne):
    return alt.Scale(domain=[-borne, 0, borne], range=[LATERITE, NEUTRE, HIVERNAGE], clamp=True)


def reponse(classe, question, texte, detail):
    st.markdown(f"""<div class="reponse {classe}"><p class="question">{question}</p>
<p class="reponse-texte">{texte}</p><p class="detail">{detail}</p></div>""", unsafe_allow_html=True)


def ruban():
    st.markdown('<div class="ruban" role="presentation">&nbsp;</div>', unsafe_allow_html=True)


def pied():
    st.markdown("""<div class="pied">Romba Abdoul Aziz, École Mohammadia d'Ingénieurs, 2026. Données : PAM (HDX),
HarvestStat Africa, FAOSTAT, CHIRPS, ERA5-Land, MODIS, ESA WorldCover, et Enquête Permanente Agricole
(EPA 2023-2024), DGESS. Prototype académique : les prévisions ne remplacent pas les bulletins officiels.</div>""",
                unsafe_allow_html=True)


# ------------------------------------------------------------------ calculs partagés
@st.cache_data
def rendements_futurs():
    f = lire("rendements_previsions_2024_2025.csv")
    if (DATA / "rendements_previsions_2026.csv").exists():
        f26 = lire("rendements_previsions_2026.csv")
        # on garde la prévision la plus tardive disponible (fin septembre si elle existe)
        rang = f26["date"].map({"fin août": 0, "fin septembre": 1})
        f26 = f26[rang == rang.max()][["fnid", "cereale", "annee", "ref5", "prevu", "ecart_pct"]]
        f = pd.concat([f, f26], ignore_index=True)
    t = lire("rendements_tests_2016_2023.csv")
    poids = t[t["date"] == "fin septembre"].groupby(["fnid", "cereale"])["superficie_ha"].mean().rename("poids")
    return f.join(poids, on=["fnid", "cereale"])


@st.cache_data
def resume_saison(annee):
    f = rendements_futurs()
    q = f[f["annee"] == annee].dropna(subset=["poids"])
    par_prov = q.groupby("fnid").apply(
        lambda g: (g["prevu"] * g["poids"]).sum() / (g["ref5"] * g["poids"]).sum() * 100 - 100, include_groups=False)
    return par_prov.rename("ecart").to_frame()


NOMS_DECADES = {18: "fin juin", 19: "10 juillet", 20: "20 juillet", 21: "fin juillet", 22: "10 août", 23: "20 août",
                24: "fin août", 25: "10 septembre", 26: "20 septembre", 27: "fin septembre", 28: "10 octobre",
                29: "20 octobre", 30: "fin octobre"}


def secheresse_2026():
    return lire("secheresse_2026.csv") if (DATA / "secheresse_2026.csv").exists() else None


def derniere_campagne():
    return int(rendements_futurs()["annee"].max())


# ------------------------------------------------------------------ pages
def page_accueil():
    ruban()
    campagne = derniere_campagne()
    saison = resume_saison(campagne)
    n_plus = int((saison["ecart"] > 0).sum())
    with st.container(key="hero"):
        g, d = st.columns([5, 6], gap="large")
        with g:
            st.markdown("<h1>Anticiper la campagne agricole au Burkina Faso</h1>", unsafe_allow_html=True)
            st.markdown('<p class="sous">Prix des céréales, sécheresse et rendements : des prévisions par province, '
                        'faites avant la récolte, à partir de données ouvertes.</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="constat">Campagne {campagne} : rendements attendus au-dessus de la moyenne récente '
                        f'dans {n_plus} provinces sur {len(saison)}.</p>', unsafe_allow_html=True)
            st.markdown('<p class="legende">Écart entre le rendement prévu (maïs, mil, sorgho, riz, pondérés par les '
                        'surfaces) et la moyenne des cinq années précédentes.</p>', unsafe_allow_html=True)
        with d:
            st.altair_chart(carte(saison, "ecart", "écart à la moyenne (%)", divergente(20), "+.0f", hauteur=400)
                            .configure_legend(labelColor="#FFFFFF", titleColor="#AEB8CF")
                            .configure_view(stroke=None), width="stretch")

    st.markdown("## Ce que disent les modèles")
    prev = lire("prix_previsions_en_cours.csv", ["date", "date_cible"])
    p3 = prev[(prev["horizon_mois"] == 3) & prev["cereale"].isin(["maïs", "mil", "sorgho"])]
    var3 = (p3["prevu"] / p3["prix_actuel"] - 1).median() * 100
    depuis, cible = p3["date"].iloc[0], p3["date_cible"].iloc[0]
    s = lire("secheresse_probabilites.csv")
    s25 = s[(s["annee"] == s["annee"].max()) & (s["decade"] == 24)]
    s26 = secheresse_2026()
    syn = lire("contrefactuel_synthese.csv")

    a, b = st.columns(2, gap="medium")
    with a:
        reponse("bonne" if var3 < 0 else "mauvaise", "Combien coûteront les céréales dans trois mois ?",
                f"{signe(var3)} % sur les céréales sèches d'ici {mois_fr(cible)}",
                f"Médiane de {p3['serie'].str.split(' [|] ').str[0].nunique()} marchés, à partir des prix de {mois_fr(depuis)}. "
                "Maïs, mil et sorgho ; intervalle à 80 % sur chaque marché.")
        st.page_link(PAGES["prix"], label="Voir les prix par marché", icon=":material/storefront:")
    with b:
        if s26 is not None:
            dern = s26[s26["decade"] == s26["decade"].max()]
            n_al = int((dern["p_cumul"] >= 0.3).sum())
            reponse("mauvaise" if n_al >= 5 else "neutre", "La saison 2026 manque-t-elle d'eau ?",
                    f"{n_al} province{'s' if n_al > 1 else ''} en alerte au {NOMS_DECADES[int(dern['decade'].iloc[0])]}",
                    f"Pluie depuis le 1er mai : {fr(dern['pct_normale'].median())} % de la normale (médiane des provinces).")
        else:
            reponse("neutre", f"La saison {int(s25['annee'].iloc[0])} a-t-elle manqué d'eau ?",
                    f"{int((s25['p_cumul'] >= 0.3).sum())} provinces en alerte fin août, "
                    f"{int(s25['y'].sum())} sécheresses observées",
                    "Probabilité que la pluie de mai à octobre finisse nettement sous la normale, mise à jour à chaque décade.")
        st.page_link(PAGES["secheresse"], label="Suivre la saison décade par décade", icon=":material/water_drop:")
    st.write("")
    c, e = st.columns(2, gap="medium")
    with c:
        f = rendements_futurs()
        q = f[(f["annee"] == campagne) & (f["cereale"] == "maïs")].dropna(subset=["poids"])
        ecart_mais = (q["prevu"] * q["poids"]).sum() / (q["ref5"] * q["poids"]).sum() * 100 - 100
        reponse("bonne" if ecart_mais > 0 else "mauvaise", "Quel rendement attendre avant la récolte ?",
                f"Maïs {campagne} : {signe(ecart_mais)} % par rapport à la moyenne récente",
                "Prévision de fin septembre. La chaleur pèse autant que la pluie ; la végétation (NDVI) est le meilleur indice.")
        st.page_link(PAGES["rendements"], label="Voir les rendements par province", icon=":material/grass:")
    with e:
        reponse("neutre", "Les mesures de décembre 2024 ont-elles fait baisser les prix ?",
                "Pas d'effet détectable au-delà de l'erreur habituelle",
                f"Écart de {signe(syn['ecart_2024_pct'].min())} à {signe(syn['ecart_2024_pct'].max())} % sur 12 mois, "
                "dans la plage des années sans mesure.")
        st.page_link(PAGES["mesures"], label="Comprendre l'analyse", icon=":material/gavel:")
    pied()


def page_prix():
    ruban()
    st.markdown("# Prix des céréales")
    st.markdown("Prix au détail sur les marchés suivis par le Programme alimentaire mondial, "
                "et prévision à 1, 3 et 6 mois avec un intervalle qui contient le vrai prix 8 fois sur 10.")
    hist = lire("prix_tests_2020_2026.csv", ["date", "date_cible"])
    prev = lire("prix_previsions_en_cours.csv", ["date", "date_cible"])

    c1, c2 = st.columns([2, 3], gap="large")
    with c1:
        cereale = st.segmented_control("Céréale", CEREALES, default="maïs") or "maïs"
    series = sorted(prev.loc[prev["cereale"] == cereale, "serie"].unique())
    with c2:
        serie = st.selectbox("Marché", series)

    p = prev[prev["serie"] == serie].sort_values("horizon_mois")
    actuel, depuis = p["prix_actuel"].iloc[0], p["date"].iloc[0]

    g, d = st.columns([7, 3], gap="large")
    with g:
        h1 = hist[(hist["serie"] == serie) & (hist["horizon_mois"] == 1)][["date_cible", "prix_reel"]]
        h1 = h1.rename(columns={"date_cible": "mois", "prix_reel": "prix"})
        futur = pd.concat([pd.DataFrame({"mois": [depuis], "prevu": [actuel], "bas": [actuel], "haut": [actuel]}),
                           p.rename(columns={"date_cible": "mois", "prevu_bas": "bas", "prevu_haut": "haut"})
                           [["mois", "prevu", "bas", "haut"]]])
        x = alt.X("mois:T", title=None, axis=alt.Axis(format="%Y", tickCount="year"))
        couches = []
        if st.toggle("Montrer ce que le modèle annonçait trois mois à l'avance"):
            h3 = hist[(hist["serie"] == serie) & (hist["horizon_mois"] == 3)].rename(columns={"date_cible": "mois"})
            couches += [alt.Chart(h3).mark_area(opacity=0.16, color=HIVERNAGE).encode(x=x, y="prevu_bas_cal:Q", y2="prevu_haut_cal:Q"),
                        alt.Chart(h3).mark_line(color=HIVERNAGE, strokeWidth=1.2).encode(x=x, y="prevu_med:Q")]
        couches += [
            alt.Chart(h1).mark_line(color=INDIGO, strokeWidth=2).encode(
                x=x, y=alt.Y("prix:Q", title="FCFA par kg", scale=alt.Scale(zero=False)),
                tooltip=[alt.Tooltip("mois:T", format="%m/%Y", title="mois"), alt.Tooltip("prix:Q", format=".0f", title="prix")]),
            alt.Chart(futur).mark_area(opacity=0.28, color=MIL).encode(x=x, y="bas:Q", y2="haut:Q"),
            alt.Chart(futur).mark_line(color="#9C7212", strokeWidth=2.2, strokeDash=[6, 3], point=alt.OverlayMarkDef(size=50, color="#9C7212")).encode(
                x=x, y="prevu:Q",
                tooltip=[alt.Tooltip("mois:T", format="%m/%Y", title="mois"), alt.Tooltip("prevu:Q", format=".0f", title="prévu"),
                         alt.Tooltip("bas:Q", format=".0f"), alt.Tooltip("haut:Q", format=".0f")]),
        ]
        st.altair_chart(alt.layer(*couches).properties(height=380), width="stretch")
        st.markdown('<p class="note">Bleu : prix observés. Or : prévision et intervalle à 80 %. '
                    'Vert : prévisions passées, pour juger le modèle sur pièces.</p>', unsafe_allow_html=True)
    with d:
        lignes = "".join(
            f"""<div class="ligne"><span class="quand">dans {r['horizon_mois']} mois, {mois_fr(r['date_cible'])}</span>
<span class="prix">{fr(r['prevu'])}</span>
<span class="fourchette">entre {fr(r['prevu_bas'])} et {fr(r['prevu_haut'])} FCFA ·
<span class="{'hausse' if r['prevu'] > actuel else 'baisse'}">{signe((r['prevu'] / actuel - 1) * 100)} %</span></span></div>"""
            for _, r in p.iterrows())
        st.markdown(f"""<div class="ticket"><div class="ligne"><span class="quand">{mois_fr(depuis)}, dernier prix connu</span>
<span class="prix">{fr(actuel)}</span><span class="fourchette">FCFA par kg, {nom_province(p['fnid'].iloc[0])}</span></div>
{lignes}</div>""", unsafe_allow_html=True)

    st.markdown(f"## Où le {cereale} va-t-il baisser ou monter ?")
    horizon = st.segmented_control("Horizon", [1, 3, 6], default=3, format_func=lambda h: f"{h} mois") or 3
    t = prev[(prev["cereale"] == cereale) & (prev["horizon_mois"] == horizon)].copy()
    t["variation"] = (t["prevu"] / t["prix_actuel"] - 1) * 100
    g, d = st.columns([1, 1], gap="large")
    with g:
        par_prov = t.groupby("fnid")[["variation"]].median()
        st.altair_chart(carte(par_prov, "variation", "variation attendue (%)",
                              alt.Scale(domain=[-30, 0, 30], range=[HIVERNAGE, NEUTRE, LATERITE], clamp=True), "+.0f"),
                        width="stretch")
        st.markdown('<p class="note">Médiane des marchés de chaque province. Gris : pas de marché suivi.</p>',
                    unsafe_allow_html=True)
    with d:
        t["marché"] = t["serie"].str.split(" \\| ").str[0]
        t["produit"] = t["serie"].str.split(" \\| ").str[1]
        t["province"] = t["fnid"].map(nom_province)
        st.dataframe(t.sort_values("variation")[["marché", "produit", "prix_actuel", "prevu", "variation"]],
                     hide_index=True, width="stretch", height=430,
                     column_config={"prix_actuel": st.column_config.NumberColumn("aujourd'hui", format="%.0f"),
                                    "prevu": st.column_config.NumberColumn("prévu", format="%.0f"),
                                    "variation": st.column_config.NumberColumn("variation", format="%+.0f %%")})

    with st.expander("Le modèle est-il fiable ?"):
        r = lire("prix_resultats.csv")
        st.dataframe(r, hide_index=True, width="stretch")
        st.markdown("Erreur moyenne en % sur 2020-2026, sur des prévisions faites sans connaître l'avenir. "
                    "Le modèle fait jeu égal avec la persistance saisonnière ; son apport est l'**intervalle**, "
                    "qui contient le vrai prix environ 8 fois sur 10. Pour le riz, surtout importé, la prévision "
                    "est la persistance saisonnière.")
    pied()


def page_secheresse():
    ruban()
    st.markdown("# Sécheresse en cours de saison")
    st.markdown("À chaque fin de décade, la probabilité que la pluie de mai à octobre finisse nettement sous la "
                "normale de la province.")
    s26 = secheresse_2026()
    if s26 is None:
        secheresse_passees()
    else:
        onglet26, onglet_passe = st.tabs(["Campagne 2026", "Saisons 1991-2025 rejouées"])
        with onglet26:
            secheresse_campagne_2026(s26)
        with onglet_passe:
            secheresse_passees()
    pied()


def secheresse_campagne_2026(s26):
    dates = sorted(s26["decade"].unique())
    d = st.select_slider("Date de décision", options=dates, value=dates[-1],
                         format_func=lambda k: NOMS_DECADES.get(int(k), str(k)), key="d26")
    g = s26[s26["decade"] == d].set_index("fnid")
    complete = "indice_pluie_provisoire" in g.columns and d == 30
    if complete:
        g["seche"] = (g["indice_pluie_provisoire"] < -1).astype(int)
    n_al = int((g["p_cumul"] >= 0.3).sum())
    med = g["pct_normale"].median()

    a, b = st.columns([3, 2], gap="large")
    with a:
        st.altair_chart(carte(g, "p_cumul", "probabilité de saison sèche",
                              alt.Scale(domain=[0, 1], range=[NEUTRE, MIL, LATERITE]), ".0%",
                              contour_col="seche" if complete else None, hauteur=470), width="stretch")
    with b:
        if complete:
            n_sec = int(g["seche"].sum())
            reponse("mauvaise" if n_sec else "bonne", "Saison 2026 complète (indice provisoire)",
                    f"{n_sec} province{'s' if n_sec > 1 else ''} en sécheresse",
                    "Pluie de mai à octobre sous −1 écart-type de la normale. Contour épais sur la carte.")
        else:
            reponse("mauvaise" if n_al >= 5 else "neutre", f"Saison 2026, {NOMS_DECADES.get(int(d), d)}",
                    f"{n_al} province{'s' if n_al > 1 else ''} au-dessus de 30 %",
                    f"Pluie tombée depuis le 1er mai : {fr(med)} % de la normale (médiane des provinces). "
                    "Sans information, on attendrait environ 15 % de risque partout.")
        top = g.sort_values("p_cumul", ascending=False).head(8).reset_index()
        top["province"] = top["fnid"].map(nom_province)
        st.dataframe(top[["province", "p_cumul", "pct_normale"]], hide_index=True, width="stretch",
                     column_config={"province": st.column_config.TextColumn("province", width="medium"),
                                    "p_cumul": st.column_config.ProgressColumn("probabilité", format="percent",
                                                                               min_value=0, max_value=1, width="small"),
                                    "pct_normale": st.column_config.NumberColumn("% normale", format="%.0f", width="small")})

    st.markdown("## Le manque d'eau en millimètres")
    st.markdown("Les agriculteurs jugent la saison sur la quantité d'eau reçue, pas sur l'écart à la normale. "
                "Cette carte montre la pluie tombée depuis le 1er mai en pourcentage de la normale de la même date.")
    g2, d2 = st.columns([3, 2], gap="large")
    with g2:
        st.altair_chart(carte(g, "pct_normale", "pluie depuis le 1er mai (% de la normale)",
                              alt.Scale(domain=[60, 100, 140], range=[LATERITE, NEUTRE, HIVERNAGE], clamp=True),
                              ".0f", hauteur=430), width="stretch")
    with d2:
        tab = g.reset_index()
        tab["province"] = tab["fnid"].map(nom_province)
        st.dataframe(tab.sort_values("pct_normale")[["province", "pluie_cumul_mm", "pct_normale"]],
                     hide_index=True, width="stretch", height=430,
                     column_config={"pluie_cumul_mm": st.column_config.NumberColumn("pluie 2026 (mm)", format="%.0f"),
                                    "pct_normale": st.column_config.NumberColumn("% normale", format="%.0f")})

    st.markdown("## Une province au fil de la saison 2026")
    fn = st.selectbox("Province", sorted(s26["fnid"].unique(), key=nom_province), format_func=nom_province, key="p26")
    q = s26[s26["fnid"] == fn].copy()
    q["date"] = q["decade"].map(NOMS_DECADES)
    ordre = [NOMS_DECADES[k] for k in sorted(q["decade"].unique())]
    seuil = alt.Chart(pd.DataFrame({"y": [0.3]})).mark_rule(color=ENCRE_DOUCE, strokeDash=[4, 4]).encode(y="y:Q")
    courbe = alt.Chart(q).mark_line(color=LATERITE, strokeWidth=2.5, point=alt.OverlayMarkDef(size=60, color=LATERITE)).encode(
        x=alt.X("date:N", sort=ordre, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("p_cumul:Q", title="probabilité", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
        tooltip=["date", alt.Tooltip("p_cumul:Q", format=".0%", title="probabilité"),
                 alt.Tooltip("pct_normale:Q", format=".0f", title="pluie (% normale)")])
    st.altair_chart((seuil + courbe).properties(height=260), width="stretch")
    st.markdown('<p class="note">Modèle de l\'étape 9 (pluie cumulée depuis le 1er mai), appris sur 1991-2025 et appliqué '
                'aux données CHIRPS de 2026.</p>', unsafe_allow_html=True)


def secheresse_passees():
    st.markdown("Chaque saison passée est rejouée par un modèle qui ne l'avait pas vue : on peut ainsi juger "
                "la fiabilité des alertes.")
    s = lire("secheresse_probabilites.csv")
    c1, c2 = st.columns([1, 3], gap="large")
    with c1:
        annee = st.selectbox("Saison", sorted(s["annee"].unique(), reverse=True), key="saison_passee")
    with c2:
        d = st.select_slider("Date de décision", options=list(DATES_DECISION), value=21,
                             format_func=lambda k: DATES_DECISION[k], key="d_passee")
    g = s[(s["annee"] == annee) & (s["decade"] == d)].set_index("fnid")
    nb_alerte, nb_obs = int((g["p_cumul"] >= 0.3).sum()), int(g["y"].sum())

    gauche, droite = st.columns([3, 2], gap="large")
    with gauche:
        st.altair_chart(carte(g, "p_cumul", "probabilité de saison sèche",
                              alt.Scale(domain=[0, 1], range=[NEUTRE, MIL, LATERITE]), ".0%", contour_col="y",
                              hauteur=470), width="stretch")
        st.markdown('<p class="note">Contour épais : provinces où la saison s\'est réellement terminée en sécheresse.</p>',
                    unsafe_allow_html=True)
    with droite:
        reponse("mauvaise" if nb_alerte else "bonne", f"{annee}, {DATES_DECISION[d]}",
                f"{nb_alerte} province{'s' if nb_alerte > 1 else ''} au-dessus de 30 %",
                f"{nb_obs} saison{'s' if nb_obs > 1 else ''} finalement sèche{'s' if nb_obs > 1 else ''} sur 45. "
                f"Sans information, on attendrait {g['p_climato'].mean():.0%} de risque partout.")
        top = g.sort_values("p_cumul", ascending=False).head(8).reset_index()
        top["province"] = top["fnid"].map(nom_province)
        top["issue"] = np.where(top["y"] == 1, "sèche", "normale")
        st.dataframe(top[["province", "p_cumul", "issue"]], hide_index=True, width="stretch",
                     column_config={"p_cumul": st.column_config.ProgressColumn("probabilité", format="percent",
                                                                               min_value=0, max_value=1),
                                    "issue": st.column_config.TextColumn("saison finale")})

    st.markdown("## Une province au fil de la saison")
    fn = st.selectbox("Province", sorted(s["fnid"].unique(), key=nom_province), format_func=nom_province,
                      key="p_passee")
    q = s[(s["annee"] == annee) & (s["fnid"] == fn)].copy()
    q["date"] = q["decade"].map(DATES_DECISION)
    seuil = alt.Chart(pd.DataFrame({"y": [0.3]})).mark_rule(color=ENCRE_DOUCE, strokeDash=[4, 4]).encode(y="y:Q")
    courbe = alt.Chart(q).mark_line(color=LATERITE, strokeWidth=2.5, point=alt.OverlayMarkDef(size=60, color=LATERITE)).encode(
        x=alt.X("date:N", sort=list(DATES_DECISION.values()), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("p_cumul:Q", title="probabilité", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
        tooltip=["date", alt.Tooltip("p_cumul:Q", format=".0%", title="probabilité")])
    st.altair_chart((seuil + courbe).properties(height=260), width="stretch")
    fin = "s'est terminée en sécheresse" if q["y"].iloc[0] == 1 else "ne s'est pas terminée en sécheresse"
    st.markdown(f"À {nom_province(fn)}, la saison {annee} {fin} "
                f"(indice de pluie {signe(q['indice_pluie_saison'].iloc[0], 2)}).")

    with st.expander("Fiabilité et limites"):
        r = lire("secheresse_resultats.csv")
        st.dataframe(r[r["methode"] == "cumul seul"].drop(columns="methode"), hide_index=True, width="stretch")
        st.markdown("""
- Fin juin, on ne connaît que 5 % de la saison : l'alerte devient fiable **à partir de la mi-août**.
- Ajouter la chaleur ou la végétation n'a pas amélioré la prévision : rien ne prévoit la pluie à venir.
- C'est une sécheresse **météorologique**, relative à la normale de chaque province. Les agriculteurs (EPA 2023)
  décrivent plutôt une sécheresse **agricole** : leur déclaration suit la pluie en millimètres
  (corrélation −0,70), pas l'écart à la normale (−0,24).
""")


def page_rendements():
    ruban()
    st.markdown("# Rendements avant la récolte")
    st.markdown("Le rendement attendu fin septembre, avant toute récolte : la moyenne des cinq dernières années, "
                "corrigée par la pluie, la chaleur et l'état de la végétation vu par satellite.")
    f = rendements_futurs()
    t = lire("rendements_tests_2016_2023.csv")
    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        cereale = st.segmented_control("Céréale", CEREALES, default="maïs", key="rdt_cer") or "maïs"
    with c2:
        campagnes = sorted(f["annee"].unique().astype(int))
        annee = st.segmented_control("Campagne", campagnes, default=campagnes[-1]) or campagnes[-1]

    q = f[(f["cereale"] == cereale) & (f["annee"] == annee)].dropna(subset=["poids"]).set_index("fnid")
    ref = (q["ref5"] * q["poids"]).sum() / q["poids"].sum()
    pre = (q["prevu"] * q["poids"]).sum() / q["poids"].sum()
    g, d = st.columns([3, 2], gap="large")
    with g:
        st.altair_chart(carte(q, "ecart_pct", "écart à la moyenne récente (%)", divergente(25), "+.0f", hauteur=470),
                        width="stretch")
    with d:
        reponse("bonne" if pre > ref else "mauvaise", f"{cereale.capitalize()}, campagne {annee}",
                f"{fr(pre, 2)} t/ha attendues, {signe((pre / ref - 1) * 100)} %",
                f"Moyenne récente : {fr(ref, 2)} t/ha. Moyenne nationale pondérée par les surfaces.")
        st.write("")
        if annee == 2026:
            st.markdown('<p class="note">Prévision faite avec les données satellites de 2026 (pluie, chaleur, NDVI). '
                        'La référence est la moyenne 2019-2023, les dernières années publiées par province : si les '
                        'bonnes récoltes de 2024 et 2025 se confirment, le niveau de 2026 est peut-être sous-estimé. '
                        'À comparer aux résultats provisoires de la DGESS.</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="note">Les chiffres officiels provisoires vont dans le même sens : production '
                        'céréalière 2024-2025 en hausse de 18 % sur 2023, et 2025-2026 en hausse de 17,6 % sur 2024, '
                        'dont une partie vient de surfaces cultivées en hausse. Le mil, prévu vers +20 %, est '
                        'probablement surestimé.</p>', unsafe_allow_html=True)

    st.markdown("## Le modèle face aux années passées")
    gt = t[(t["cereale"] == cereale) & (t["date"] == "fin septembre")].dropna(subset=["superficie_ha"])
    def pond(x, col):
        return (x[col] * x["superficie_ha"]).sum() / x["superficie_ha"].sum()
    nat = gt.groupby("annee").apply(lambda x: pd.Series({
        "observé": pond(x, "rendement_t_ha"), "moyenne des 5 ans": pond(x, "ref5"),
        "prévision fin septembre": pond(x, "prevu_B climat + NDVI")}), include_groups=False).reset_index()
    long = nat.melt("annee", var_name="série", value_name="t/ha")
    st.altair_chart(alt.Chart(long).mark_line(strokeWidth=2.2, point=alt.OverlayMarkDef(size=55)).encode(
        x=alt.X("annee:O", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("t/ha:Q", title="t/ha", scale=alt.Scale(zero=False)),
        color=alt.Color("série:N", title=None, scale=alt.Scale(
            domain=["observé", "moyenne des 5 ans", "prévision fin septembre"], range=[INDIGO, "#A7AFBD", HIVERNAGE])),
        tooltip=["annee", "série", alt.Tooltip("t/ha:Q", format=".2f")]).properties(height=300), width="stretch")
    st.markdown('<p class="note">Rendement national, test 2016-2023. Les rendements 2023 sont corrigés avec l\'Enquête '
                'Permanente Agricole (EPA 2023-2024), DGESS.</p>', unsafe_allow_html=True)

    st.markdown("## Ce qui fait le rendement")
    c = lire("rendements_coefficients.csv").set_index("variable")
    grp = pd.DataFrame({
        "pluie": c.loc[["cumul_z", "pluie_recente_rel"]].sum(),
        "végétation (NDVI)": c.loc[[v for v in ["ndvi_max_anom", "ndvi_recent_anom"] if v in c.index]].sum(),
        "chaleur": c.loc["tmax_anom"], "décades sèches": c.loc["decades_seches"]}).reset_index(names="céréale")
    lg = grp.melt("céréale", var_name="facteur", value_name="effet")
    st.altair_chart(alt.Chart(lg).mark_bar(cornerRadius=3).encode(
        x=alt.X("effet:Q", title="effet d'un écart à la normale (t/ha)", axis=alt.Axis(format="+.2f")),
        y=alt.Y("facteur:N", title=None, sort=["chaleur", "végétation (NDVI)", "décades sèches", "pluie"]),
        yOffset=alt.YOffset("céréale:N", sort=CEREALES),
        color=alt.Color("céréale:N", sort=CEREALES, scale=alt.Scale(domain=CEREALES,
                        range=[MIL, "#7B5C2E", LATERITE, "#4E79A7"]), title=None),
        tooltip=["céréale", "facteur", alt.Tooltip("effet:Q", format="+.3f")]).properties(height=320), width="stretch")
    st.markdown("Une saison plus chaude que la normale fait perdre du rendement à toutes les céréales, autant qu'une "
                "végétation vigoureuse en fait gagner. Une fois la chaleur et la végétation connues, la pluie n'ajoute "
                "presque rien, sauf pour le riz, cultivé en bas-fond.")
    with st.expander("Le modèle est-il fiable ?"):
        st.dataframe(lire("rendements_resultats.csv"), hide_index=True, width="stretch")
        st.markdown("Fin septembre, le modèle bat la moyenne des 5 ans pour les quatre céréales (+0,4 à +7 %) "
                    "et repère 22 à 42 % des mauvaises années.")
    pied()


def page_mesures():
    ruban()
    st.markdown("# Les mesures de décembre 2024 ont-elles fait baisser les prix ?")
    st.markdown("En décembre 2024, le gouvernement interdit l'exportation des céréales, renforce la SONAGESS et "
                "contrôle les prix. Pour mesurer leur effet, le modèle des prix, entraîné **avant** ces mesures, "
                "prévoit les douze mois suivants comme si rien n'avait changé. On compare aux prix observés, et on "
                "refait l'exercice pour neuf années sans mesure.")
    e = lire("contrefactuel_ecarts.csv", ["date_cible"])
    med = e.groupby(["cereale", "annee_origine", "horizon_mois"])["ecart_pct"].median().reset_index()
    med["série"] = np.where(med["annee_origine"] == 2024, "depuis novembre 2024", "années sans mesure")
    graph = alt.Chart(med).mark_line().encode(
        x=alt.X("horizon_mois:Q", title="mois après novembre", axis=alt.Axis(tickCount=6)),
        y=alt.Y("ecart_pct:Q", title="prix observé / prévu (%)"),
        detail="annee_origine:N",
        color=alt.Color("série:N", title=None, scale=alt.Scale(domain=["depuis novembre 2024", "années sans mesure"],
                                                                range=[LATERITE, "#BCC3CF"])),
        strokeWidth=alt.condition("datum.annee_origine == 2024", alt.value(3.2), alt.value(1.2)),
        tooltip=[alt.Tooltip("annee_origine:N", title="depuis novembre"), "horizon_mois",
                 alt.Tooltip("ecart_pct:Q", format="+.1f", title="écart (%)")]
    ).properties(width=290, height=280).facet(column=alt.Column("cereale:N", title=None))
    st.altair_chart(graph)

    a, b, c = st.columns(3, gap="medium")
    with a:
        reponse("neutre", "Décembre 2024 à juin 2025", "Les prix suivent le scénario sans mesure",
                "Écart de 0 à −7 %, comme les années ordinaires.")
    with b:
        reponse("neutre", "Août à novembre 2025", "L'écart se creuse jusqu'à −26 %",
                "C'est l'arrivée de la récolte record de 2025, que le scénario ne pouvait pas connaître.")
    with c:
        reponse("neutre", "Conclusion", "Pas d'effet détectable",
                "Vu l'erreur habituelle du modèle, seul un effet de plus de 15 à 30 % aurait été visible.")
    st.write("")
    with st.expander("Les chiffres"):
        st.dataframe(lire("contrefactuel_synthese.csv"), hide_index=True, width="stretch")
    pied()


def page_methodes():
    ruban()
    st.markdown("# Méthodes, sources et limites")
    g, d = st.columns(2, gap="large")
    with g:
        st.markdown("""
### Sources
- **Prix** : Programme alimentaire mondial, via Humanitarian Data Exchange. 64 marchés, 1992-2026.
- **Rendements** : HarvestStat Africa (FEWS NET), validé avec FAOSTAT. 45 provinces.
- **Pluie** : CHIRPS v3. **Chaleur et humidité** : ERA5-Land. **Végétation** : MODIS NDVI.
  **Zones cultivées** : ESA WorldCover. Extraction avec Google Earth Engine.
- **Enquête Permanente Agricole (EPA 2023-2024), DGESS** : agrégats par province pour corriger les rendements 2023
  et analyser les pertes déclarées.

### Règles de validation
- Aucune prévision n'utilise une information postérieure à sa date.
- Chaque modèle est comparé à une référence simple : persistance des prix, fréquence habituelle des sécheresses,
  moyenne des cinq ans.
- Les modèles sont ré-entraînés chaque année pour suivre les changements : nouvelle méthode de HarvestStat en 2015,
  insécurité depuis 2019.
""")
    with d:
        st.markdown("""
### Ce que la plateforme ne dit pas
- **Ravageurs et maladies** : aucune donnée publique d'incidence. L'indice météo construit n'a pas été validé par
  les pertes déclarées dans l'EPA 2023 : il reflète surtout la qualité de la saison.
- **Décisions publiques** : interdictions d'exporter, stocks et contrôle des prix ne sont pas dans les variables.
- **Variétés et systèmes** : les rendements sont par province, sans distinction de variété ni entre pluvial,
  bas-fond et irrigué.
- **Découpage** : les calculs portent sur les 45 provinces d'avant 2025, affichées avec leur nom actuel.
""")
    pied()


PAGES = {
    "accueil": st.Page(page_accueil, title="Accueil", icon=":material/home:", default=True),
    "prix": st.Page(page_prix, title="Prix", icon=":material/storefront:", url_path="prix"),
    "secheresse": st.Page(page_secheresse, title="Sécheresse", icon=":material/water_drop:", url_path="secheresse"),
    "rendements": st.Page(page_rendements, title="Rendements", icon=":material/grass:", url_path="rendements"),
    "mesures": st.Page(page_mesures, title="Mesures de 2024", icon=":material/gavel:", url_path="mesures"),
    "methodes": st.Page(page_methodes, title="Méthodes", icon=":material/menu_book:", url_path="methodes"),
}
st.navigation(list(PAGES.values()), position="top").run()
