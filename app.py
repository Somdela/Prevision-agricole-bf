"""
Anticiper la campagne agricole au Burkina Faso
Tableau de bord de démonstration · Romba Abdoul Aziz · École Mohammadia d'Ingénieurs

L'application ne calcule rien : elle lit les fichiers CSV produits dans Colab (étapes 8 à 12)
et les affiche. Pour mettre à jour un résultat, on remplace le fichier dans data/.
"""
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Anticiper la campagne agricole · Burkina Faso", page_icon="🌾", layout="wide")
ICI = Path(__file__).parent
# Les CSV peuvent être dans un dossier data/ ou directement à côté de app.py
DATA = ICI / "data" if (ICI / "data").is_dir() else ICI

VERT, TERRE, GRIS, OR = "#2F6B4F", "#A8470F", "#9A948A", "#C9962B"
CEREALES = ["maïs", "mil", "sorgho", "riz"]
DATES_DECISION = {18: "fin juin", 19: "10 juillet", 20: "20 juillet", 21: "fin juillet",
                  22: "10 août", 23: "20 août", 24: "fin août"}


# ---------------------------------------------------------------- données
@st.cache_data
def lire(nom, dates=()):
    return pd.read_csv(DATA / nom, parse_dates=list(dates))


@st.cache_data
def provinces():
    p = lire("provinces.csv")
    p["nom"] = np.where(p["changement"] == "inchangée", p["province_2025"],
                        p["province_2025"] + " (ex-" + p["province_ancienne"] + ")")
    return p.set_index("fnid")


PROV = provinces()


def nom_province(fnid):
    return PROV["nom"].get(fnid, fnid)


MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def mois_fr(d):
    return f"{MOIS[d.month - 1]} {d.year}"


def pct(x):
    return f"{x:+.0f} %"


# ---------------------------------------------------------------- pages
def page_accueil():
    st.title("Anticiper la campagne agricole au Burkina Faso")
    st.markdown("Prévision par apprentissage automatique de la **sécheresse**, des **rendements** et des "
                "**prix des céréales**, et analyse du **risque ravageurs et maladies**.")
    st.caption("Romba Abdoul Aziz · École Mohammadia d'Ingénieurs · projet de data science, 2026")

    prev = lire("prix_previsions_en_cours.csv", ["date", "date_cible"])
    p3 = prev[(prev["horizon_mois"] == 3) & prev["cereale"].isin(["maïs", "mil", "sorgho"])]
    var3 = (p3["prevu"] / p3["prix_actuel"] - 1).median() * 100
    sech = lire("secheresse_resultats.csv")
    auc = sech[(sech["methode"] == "cumul seul") & (sech["date"] == "20 août")]["AUC"].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prix des céréales sèches dans 3 mois", pct(var3), help="Médiane des marchés, depuis août 2026")
    c2.metric("Sécheresse : fiabilité au 20 août", f"AUC {auc:.2f}", help="1 = parfait, 0,5 = hasard")
    c3.metric("Séries de prix suivies", f"{prev['serie'].nunique()}")
    c4.metric("Provinces", "45", help="Anciennes provinces ; noms du découpage de 2025")

    st.markdown("""
#### Ce que montre ce tableau de bord

| Page | Question | Méthode retenue |
| --- | --- | --- |
| **Prix** | Quel prix dans 1, 3 et 6 mois sur chaque marché ? | Gradient boosting corrigeant la persistance saisonnière, ré-entraîné chaque année, intervalle calibré à 80 % |
| **Sécheresse** | La saison finira-t-elle anormalement sèche ? | Pluie cumulée depuis le 1er mai, mise à jour à chaque décade |
| **Rendements** | Quel rendement attendre avant la récolte ? | Moyenne des 5 ans ajustée par le climat et la végétation (NDVI) |
| **Mesures de 2024** | Les mesures de décembre 2024 ont-elles fait baisser les prix ? | Contrefactuel et test placebo |

Les modèles sont calculés dans Google Colab ; cette application affiche leurs résultats.
""")


def page_prix():
    st.header("Prix des céréales au détail")
    hist = lire("prix_tests_2020_2026.csv", ["date", "date_cible"])
    prev = lire("prix_previsions_en_cours.csv", ["date", "date_cible"])

    col1, col2 = st.columns([1, 2])
    cereale = col1.selectbox("Céréale", CEREALES)
    series = sorted(prev.loc[prev["cereale"] == cereale, "serie"].unique())
    serie = col2.selectbox("Marché et produit", series)

    p = prev[prev["serie"] == serie].sort_values("horizon_mois")
    actuel = p["prix_actuel"].iloc[0]
    depuis = p["date"].iloc[0]
    st.caption(f"Dernier prix connu : {mois_fr(depuis)}, province de {nom_province(p['fnid'].iloc[0])}")
    cols = st.columns(4)
    cols[0].metric(f"Prix en {depuis:%m/%Y}", f"{actuel:.0f} FCFA/kg")
    for col, (_, r) in zip(cols[1:], p.iterrows()):
        col.metric(f"Dans {r['horizon_mois']} mois ({r['date_cible']:%m/%Y})", f"{r['prevu']:.0f} FCFA/kg",
                   f"{(r['prevu'] / actuel - 1) * 100:+.0f} %", delta_color="inverse",
                   help=f"Intervalle à 80 % : {r['prevu_bas']:.0f} à {r['prevu_haut']:.0f} FCFA/kg")

    h1 = hist[(hist["serie"] == serie) & (hist["horizon_mois"] == 1)][["date_cible", "prix_reel"]]
    h1 = h1.rename(columns={"date_cible": "mois", "prix_reel": "prix"})
    futur = pd.concat([pd.DataFrame({"mois": [depuis], "prevu": [actuel], "bas": [actuel], "haut": [actuel]}),
                       p.rename(columns={"date_cible": "mois", "prevu_bas": "bas", "prevu_haut": "haut"})
                       [["mois", "prevu", "bas", "haut"]]])

    base = alt.Chart(h1).mark_line(color="black").encode(
        x=alt.X("mois:T", title=None, axis=alt.Axis(format="%m/%Y")), y=alt.Y("prix:Q", title="FCFA/kg", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("mois:T", format="%m/%Y"), alt.Tooltip("prix:Q", format=".0f")])
    bande = alt.Chart(futur).mark_area(opacity=0.25, color=TERRE).encode(x="mois:T", y="bas:Q", y2="haut:Q")
    ligne = alt.Chart(futur).mark_line(color=TERRE, point=True, strokeDash=[5, 3]).encode(
        x="mois:T", y="prevu:Q",
        tooltip=[alt.Tooltip("mois:T", format="%m/%Y"), alt.Tooltip("prevu:Q", format=".0f"),
                 alt.Tooltip("bas:Q", format=".0f"), alt.Tooltip("haut:Q", format=".0f")])
    couches = [base, bande, ligne]
    if st.checkbox("Afficher ce que le modèle prévoyait 3 mois à l'avance (2020-2026)"):
        h3 = hist[(hist["serie"] == serie) & (hist["horizon_mois"] == 3)]
        couches.insert(0, alt.Chart(h3).mark_area(opacity=0.18, color=VERT).encode(
            x="date_cible:T", y="prevu_bas_cal:Q", y2="prevu_haut_cal:Q"))
        couches.insert(1, alt.Chart(h3).mark_line(color=VERT, strokeWidth=1).encode(
            x="date_cible:T", y="prevu_med:Q"))
    st.altair_chart(alt.layer(*couches).properties(height=380), width="stretch")
    st.caption("Noir : prix observés (PAM). Orange : prévision et intervalle à 80 %. "
               "Vert (option) : prévision faite 3 mois avant et son intervalle.")

    st.subheader(f"Tous les marchés : {cereale}")
    horizon = st.radio("Horizon", [1, 3, 6], index=1, horizontal=True, format_func=lambda h: f"{h} mois")
    t = prev[(prev["cereale"] == cereale) & (prev["horizon_mois"] == horizon)].copy()
    t["marché"] = t["serie"]
    t["province"] = t["fnid"].map(nom_province)
    t["variation"] = (t["prevu"] / t["prix_actuel"] - 1) * 100
    t["intervalle à 80 %"] = t["prevu_bas"].round(0).astype(int).astype(str) + " – " + \
        t["prevu_haut"].round(0).astype(int).astype(str)
    st.dataframe(t[["marché", "province", "prix_actuel", "prevu", "variation", "intervalle à 80 %"]]
                 .sort_values("variation"), hide_index=True, width="stretch",
                 column_config={"prix_actuel": st.column_config.NumberColumn("prix actuel", format="%.0f"),
                                "prevu": st.column_config.NumberColumn("prévu", format="%.0f"),
                                "variation": st.column_config.NumberColumn("variation (%)", format="%+.0f")})

    with st.expander("Fiabilité du modèle (test 2020-2026)"):
        r = lire("prix_resultats.csv")
        st.dataframe(r, hide_index=True, width="stretch")
        st.markdown("Erreur moyenne en % (MAPE). Le modèle fait jeu égal avec la persistance saisonnière ; "
                    "son apport principal est l'**intervalle calibré**, qui couvre environ 80 % des prix réels. "
                    "Pour le riz, surtout importé, la prévision est la persistance saisonnière.")


def page_secheresse():
    st.header("Sécheresse en cours de saison")
    st.markdown("Probabilité que la pluie de mai à octobre finisse **sous la normale** (indice < −1), "
                "estimée à partir de la pluie tombée depuis le 1er mai. Chaque année est prévue par un modèle "
                "qui ne l'a pas vue (validation croisée par année).")
    s = lire("secheresse_probabilites.csv")
    col1, col2 = st.columns(2)
    annee = col1.selectbox("Saison", sorted(s["annee"].unique(), reverse=True))
    d = col2.select_slider("Date de décision", options=list(DATES_DECISION), value=21,
                           format_func=lambda k: DATES_DECISION[k])

    g = s[(s["annee"] == annee) & (s["decade"] == d)].copy()
    g["province"] = g["fnid"].map(nom_province)
    g["issue"] = np.where(g["y"] == 1, "sécheresse observée", "pas de sécheresse")
    nb = int(g["y"].sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Provinces à plus de 30 %", int((g["p_cumul"] >= 0.3).sum()))
    c2.metric("Sécheresses finalement observées", nb)
    c3.metric("Probabilité habituelle", f"{g['p_climato'].mean():.0%}")

    barres = alt.Chart(g).mark_bar().encode(
        y=alt.Y("province:N", sort="-x", title=None, axis=alt.Axis(labelOverlap=False, labelLimit=220)),
        x=alt.X("p_cumul:Q", title="probabilité de sécheresse", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
        color=alt.Color("issue:N", scale=alt.Scale(domain=["sécheresse observée", "pas de sécheresse"],
                                                   range=[TERRE, "#9BB5A4"]), title=None),
        tooltip=["province", alt.Tooltip("p_cumul:Q", format=".0%"), "issue"])
    seuil = alt.Chart(pd.DataFrame({"x": [0.3]})).mark_rule(strokeDash=[4, 3], color="grey").encode(x="x:Q")
    st.altair_chart((barres + seuil).properties(height=950), width="stretch")

    st.subheader("Une province au fil de la saison")
    fn = st.selectbox("Province", sorted(s["fnid"].unique(), key=nom_province), format_func=nom_province)
    q = s[(s["annee"] == annee) & (s["fnid"] == fn)].copy()
    q["date"] = q["decade"].map(DATES_DECISION)
    st.altair_chart(alt.Chart(q).mark_line(point=True, color=TERRE).encode(
        x=alt.X("date:N", sort=list(DATES_DECISION.values()), title=None),
        y=alt.Y("p_cumul:Q", title="probabilité", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
        tooltip=["date", alt.Tooltip("p_cumul:Q", format=".0%")]).properties(height=260), width="stretch")
    issue = "s'est terminée **en sécheresse**" if q["y"].iloc[0] == 1 else "ne s'est **pas** terminée en sécheresse"
    st.markdown(f"La saison {annee} {issue} (indice de pluie {q['indice_pluie_saison'].iloc[0]:+.2f}).")

    with st.expander("Fiabilité et limites"):
        r = lire("secheresse_resultats.csv")
        st.dataframe(r[r["methode"] == "cumul seul"].drop(columns="methode"), hide_index=True,
                     width="stretch")
        st.markdown("""
- Fin juin, on ne connaît que 5 % de la saison : le signal est faible. L'alerte devient fiable **à partir de la mi-août**.
- Les autres variables (chaleur, NDVI) n'ont pas amélioré la prévision : rien ne prévoit la pluie à venir.
- Il s'agit d'une sécheresse **météorologique** (écart à la normale de la province). Les agriculteurs de l'EPA 2023
  déclarent plutôt une sécheresse **agricole**, liée à la quantité d'eau absolue (corrélation −0,70 avec la pluie
  de juillet-septembre en mm, contre −0,24 avec l'indice relatif).
""")


def page_rendements():
    st.header("Rendements avant la récolte")
    t = lire("rendements_tests_2016_2023.csv")
    f = lire("rendements_previsions_2024_2025.csv")
    cereale = st.selectbox("Céréale", CEREALES)

    st.subheader("Test 2016-2023 : rendement national")
    g = t[(t["cereale"] == cereale) & (t["date"] == "fin septembre")].dropna(subset=["superficie_ha"])
    def pond(x, col):
        return (x[col] * x["superficie_ha"]).sum() / x["superficie_ha"].sum()
    nat = g.groupby("annee").apply(lambda x: pd.Series({
        "observé": pond(x, "rendement_t_ha"), "moyenne des 5 ans": pond(x, "ref5"),
        "modèle (climat + NDVI)": pond(x, "prevu_B climat + NDVI")}), include_groups=False).reset_index()
    long = nat.melt("annee", var_name="série", value_name="t/ha")
    st.altair_chart(alt.Chart(long).mark_line(point=True).encode(
        x=alt.X("annee:O", title=None), y=alt.Y("t/ha:Q", scale=alt.Scale(zero=False)),
        color=alt.Color("série:N", scale=alt.Scale(domain=["observé", "moyenne des 5 ans", "modèle (climat + NDVI)"],
                                                    range=["black", GRIS, VERT])),
        tooltip=["annee", "série", alt.Tooltip("t/ha:Q", format=".2f")]).properties(height=320),
        width="stretch")
    st.caption("Prévision faite fin septembre, avant la récolte. Rendements 2023 corrigés avec l'Enquête Permanente "
               "Agricole (EPA 2023-2024), DGESS.")

    st.subheader("Prévisions pour les campagnes 2024 et 2025")
    annee = st.radio("Campagne", [2024, 2025], horizontal=True)
    poids = t[(t["cereale"] == cereale) & (t["date"] == "fin septembre")].groupby("fnid")["superficie_ha"].mean()
    q = f[(f["cereale"] == cereale) & (f["annee"] == annee)].copy()
    q["poids"] = q["fnid"].map(poids)
    q = q.dropna(subset=["poids"])
    ref = (q["ref5"] * q["poids"]).sum() / q["poids"].sum()
    pre = (q["prevu"] * q["poids"]).sum() / q["poids"].sum()
    c1, c2 = st.columns(2)
    c1.metric("Moyenne récente (national)", f"{ref:.2f} t/ha")
    c2.metric(f"Prévu pour {annee}", f"{pre:.2f} t/ha", f"{(pre / ref - 1) * 100:+.0f} %")
    q["province"] = q["fnid"].map(nom_province)
    st.altair_chart(alt.Chart(q).mark_bar().encode(
        y=alt.Y("province:N", sort="-x", title=None, axis=alt.Axis(labelOverlap=False, labelLimit=220)),
        x=alt.X("ecart_pct:Q", title="écart à la moyenne récente (%)"),
        color=alt.condition("datum.ecart_pct < 0", alt.value(TERRE), alt.value(VERT)),
        tooltip=["province", alt.Tooltip("ref5:Q", format=".2f", title="moyenne"),
                 alt.Tooltip("prevu:Q", format=".2f", title="prévu"), alt.Tooltip("ecart_pct:Q", format="+.0f")])
        .properties(height=950), width="stretch")
    st.info("Les chiffres officiels provisoires vont dans le même sens : production céréalière 2024-2025 en hausse de "
            "18 % sur 2023, et 2025-2026 en hausse de 17,6 % sur 2024 (une partie vient de surfaces en hausse). "
            "Le mil prévu à +20 % est sans doute trop optimiste : sa production officielle 2025 n'est qu'à +8 % "
            "au-dessus de la moyenne.")

    with st.expander("Fiabilité du modèle (test 2016-2023)"):
        st.dataframe(lire("rendements_resultats.csv"), hide_index=True, width="stretch")
        st.markdown("Erreurs en t/ha et gain sur la moyenne des 5 ans (%). Fin septembre, le modèle avec NDVI bat la "
                    "moyenne pour les quatre céréales (+0,4 à +7 %) et repère 22 à 42 % des mauvaises années.")

    with st.expander("Ce qui fait le rendement (coefficients du modèle)"):
        c = lire("rendements_coefficients.csv").set_index("variable")
        grp = pd.DataFrame({
            "pluie": c.loc[["cumul_z", "pluie_recente_rel"]].sum(),
            "NDVI (végétation)": c.loc[[v for v in ["ndvi_max_anom", "ndvi_recent_anom"] if v in c.index]].sum(),
            "chaleur": c.loc["tmax_anom"], "décades sèches": c.loc["decades_seches"]}).reset_index(names="céréale")
        lg = grp.melt("céréale", var_name="facteur", value_name="effet (t/ha)")
        st.altair_chart(alt.Chart(lg).mark_bar().encode(
            x=alt.X("effet (t/ha):Q"), y=alt.Y("facteur:N", title=None), color=alt.Color("céréale:N"),
            yOffset="céréale:N").properties(height=300), width="stretch")
        st.markdown("Effet d'un écart-type de chaque facteur. **La chaleur pèse autant que la pluie** : "
                    "elle fait baisser le rendement de toutes les céréales, le NDVI le fait monter.")


def page_mesures():
    st.header("Les mesures de décembre 2024 ont-elles fait baisser les prix ?")
    st.markdown("""
En décembre 2024, le gouvernement annonce l'interdiction d'exporter les céréales, le renforcement de la SONAGESS
et le contrôle des prix. Le modèle des prix, entraîné **avant** ces mesures, prévoit les 12 mois suivants comme si
rien n'avait changé. On compare ensuite aux prix observés, et on refait l'exercice pour les années **sans** mesure
(test placebo).
""")
    e = lire("contrefactuel_ecarts.csv", ["date_cible"])
    med = e.groupby(["cereale", "annee_origine", "horizon_mois"])["ecart_pct"].median().reset_index()
    med["année"] = np.where(med["annee_origine"] == 2024, "depuis nov. 2024 (mesures)", "années sans mesure")
    graph = alt.Chart(med).mark_line().encode(
        x=alt.X("horizon_mois:Q", title="mois après novembre"),
        y=alt.Y("ecart_pct:Q", title="prix observé / prévu − 1 (%)"),
        detail="annee_origine:N",
        color=alt.Color("année:N", scale=alt.Scale(domain=["depuis nov. 2024 (mesures)", "années sans mesure"],
                                                   range=[TERRE, "#C9C3B8"]), title=None,
                        legend=alt.Legend(orient="bottom")),
        strokeWidth=alt.condition("datum.annee_origine == 2024", alt.value(3), alt.value(1)),
        tooltip=["annee_origine", "horizon_mois", alt.Tooltip("ecart_pct:Q", format="+.1f")]
    ).properties(width=240, height=260).facet(column=alt.Column("cereale:N", title=None))
    st.altair_chart(graph)

    st.dataframe(lire("contrefactuel_synthese.csv"), hide_index=True, width="stretch")
    st.markdown("""
**Conclusion**

- De décembre 2024 à juin 2025, les prix suivent le contrefactuel : **pas d'effet visible**.
- L'écart se creuse à partir d'août 2025, au moment de la récolte record de 2025, que le contrefactuel ne pouvait pas connaître.
- Sur 12 mois, l'écart (−6 à −9 %) reste dans la plage des années sans mesure : **on ne détecte pas d'effet**.
- Seuil de détection : vu l'erreur habituelle du modèle, seul un effet supérieur à environ **15-30 %** serait visible.
""")


def page_methodes():
    st.header("Méthodes, sources et limites")
    st.markdown("""
#### Sources (données ouvertes)
- **Prix** : Programme alimentaire mondial, via Humanitarian Data Exchange (HDX), 64 marchés, 1992-2026.
- **Rendements** : HarvestStat Africa (FEWS NET, UCSB), 45 provinces, validé avec FAOSTAT.
- **Pluie** : CHIRPS v3 ; **température et humidité** : ERA5-Land (ECMWF) ; **végétation** : MODIS NDVI (NASA) ;
  **zones cultivées** : ESA WorldCover. Extraction par Google Earth Engine.
- **Enquête Permanente Agricole (EPA 2023-2024), DGESS** : agrégats par province ayant servi à corriger les rendements
  2023 (superficies manquantes dans HarvestStat) et à analyser les pertes déclarées. Les microdonnées ne figurent pas
  dans cette application.

#### Principes de validation
- Jamais d'information future : chaque prévision n'utilise que ce qui était connu à sa date.
- Comparaison systématique à une référence simple (persistance, climatologie, moyenne des 5 ans).
- Ré-entraînement annuel pour suivre les changements (rupture de méthode HarvestStat en 2015, insécurité depuis 2019).

#### Limites
- **Ravageurs et maladies** : aucune donnée publique d'incidence. L'indice météo construit n'a pas été validé par les
  pertes déclarées dans l'EPA 2023 ; il traduit surtout la qualité de la saison.
- **Prix** : les décisions publiques (exportations, stocks, contrôle des prix) et l'insécurité ne sont que partiellement
  représentées.
- **Rendements** : niveau province, pas de distinction par variété ni par système (pluvial, bas-fond, irrigué).
- Les provinces sont celles d'avant le découpage de 2025, affichées avec leurs nouveaux noms.
""")


PAGES = {"Accueil": page_accueil, "Prix": page_prix, "Sécheresse": page_secheresse,
         "Rendements": page_rendements, "Mesures de 2024": page_mesures, "Méthodes et limites": page_methodes}
st.sidebar.title("🌾 Campagne agricole")
choix = st.sidebar.radio("Page", list(PAGES))
st.sidebar.caption("Burkina Faso · données ouvertes · prototype académique")
PAGES[choix]()
