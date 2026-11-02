from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from pipeline import OUT_DIR

st.set_page_config(page_title="RidePulse | Punjab Mobility", page_icon="◉", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}.stApp{background:#f5f7fb;color:#13233f}
[data-testid="stSidebar"]{background:#101d36;color:#eef3ff}[data-testid="stSidebar"] *{color:#eef3ff}
.hero{padding:32px 36px;border-radius:20px;background:linear-gradient(115deg,#10203f,#193b69);color:white;margin-bottom:24px}
.hero h1{font:800 36px Manrope;margin:4px 0 10px}.eyebrow{letter-spacing:2px;text-transform:uppercase;font-size:11px;color:#77d4cc;font-weight:700}
.hero p{color:#d4deed;font-size:16px;max-width:850px}.metric{background:white;border:1px solid #e4eaf3;border-radius:14px;padding:18px 20px;min-height:100px}
.metric-label{font-size:12px;color:#71809a;text-transform:uppercase;letter-spacing:.8px}.metric-value{font:700 27px Manrope;color:#193354;margin-top:8px}
.note{background:#fff3df;border-left:4px solid #df9a24;padding:14px 18px;border-radius:8px;color:#674c18}
h1,h2,h3{font-family:Manrope,sans-serif}.block-container{padding-top:2rem;max-width:1440px}
</style>""", unsafe_allow_html=True)

DATA_PATH = OUT_DIR / "census_2011_commute_modes.csv"
TABLEAU_PATH = Path(__file__).parent / "tableau" / "data" / "census_2011_commute_modes.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH) if DATA_PATH.exists() else pd.DataFrame()

data = load_data()
with st.sidebar:
    st.markdown("## ◉ RidePulse")
    st.caption("REAL CENSUS COMMUTE DATA")
    st.caption("Punjab districts + Chandigarh · Census 2011")
    page = st.radio("Workspace", ["Overview", "Data Explorer", "Analytics & Insights", "Tableau BI", "About Project"], label_visibility="collapsed")
    st.divider()
    st.caption("This dataset measures work commuting. It contains no ride-hailing bookings.")

def hero(title, subtitle):
    st.markdown(f'<div class="hero"><div class="eyebrow">Official Census 2011 mobility context</div><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)
def metric(label, value):
    st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)
def filtered_data():
    view = data.copy()
    areas = st.multiselect("District / UT aggregate", sorted(view.area_name.dropna().unique()), default=sorted(view.area_name.dropna().unique()))
    res = st.multiselect("Residence area", ["Urban", "Rural", "Total"], default=["Urban"])
    return view[view.area_name.isin(areas) & view.residence_area.isin(res)]

if page == "Overview":
    hero("Real mobility data. Clear limits.", "Explore Census 2011 work-commute mode and distance counts for selected Punjab districts and Chandigarh.")
    st.markdown('<div class="note"><b>Scope:</b> this is a real, official Census dataset about workers’ journeys to work. It is not ride-hailing or booking data. Counts describe 2011, and Mohali is represented by Sahibzada Ajit Singh Nagar district totals.</div>', unsafe_allow_html=True)
    if data.empty:
        st.error("The Census workbooks are present, but the normalized data is not built yet. Run `python pipeline.py` from the project folder.")
    else:
        urban = data[(data.residence_area == "Urban") & (data.mode_of_travel == "All Modes")]
        cards=st.columns(4)
        vals=[("Urban workers counted",f"{int(urban.total_persons.sum()):,}"),("Geographic aggregates",str(urban.area_name.nunique())),("Census year",str(int(data.year.max()))),("Distinct travel modes",str(data.loc[data.mode_of_travel.ne('All Modes'),'mode_of_travel'].nunique()))]
        for col,(label,value) in zip(cards,vals):
            with col: metric(label,value)
        st.subheader("Urban commute modes by district")
        plot=data[(data.residence_area=="Urban") & ~data.mode_of_travel.eq("All Modes")]
        st.plotly_chart(px.bar(plot,x="area_name",y="total_persons",color="mode_of_travel",barmode="stack",labels={"area_name":"District / UT","total_persons":"Workers","mode_of_travel":"Mode"},color_discrete_sequence=px.colors.qualitative.Safe),width="stretch")
    st.caption("Source: Office of the Registrar General & Census Commissioner, Population Census 2011, Table B-28. See About Project for citations and limitations.")
elif page == "Data Explorer":
    hero("Explore the Census tables.", "Filter real aggregated commuting records and export the visible rows.")
    if data.empty: st.info("Run `python pipeline.py` to normalize the downloaded official Excel workbooks.")
    else:
        view=filtered_data()
        modes=st.multiselect("Mode of travel",sorted(view.mode_of_travel.unique()),default=sorted(m for m in view.mode_of_travel.unique() if m != "All Modes"))
        view=view[view.mode_of_travel.isin(modes)]
        st.caption(f"{len(view):,} rows · Census 2011")
        st.dataframe(view,width="stretch",hide_index=True)
        st.download_button("Download filtered CSV",view.to_csv(index=False).encode(),"ridepulse_census_commute_filtered.csv","text/csv")
elif page == "Analytics & Insights":
    hero("Compare commute patterns.", "Analyze only the modes, distances and demographic counts present in the Census source.")
    if data.empty: st.info("Run `python pipeline.py` to prepare analysis data.")
    else:
        view=filtered_data()
        view=view[~view.mode_of_travel.eq("All Modes")]
        st.subheader("Mode share within selected aggregates")
        st.plotly_chart(px.bar(view,x="area_name",y="mode_share_pct",color="mode_of_travel",barmode="stack",labels={"area_name":"District / UT","mode_share_pct":"Share of all modes (%)","mode_of_travel":"Mode"},color_discrete_sequence=px.colors.qualitative.Safe),width="stretch")
        st.subheader("Gender counts by commute mode")
        gender=view.melt(id_vars=["area_name","mode_of_travel"],value_vars=["total_male","total_female"],var_name="Gender",value_name="Workers")
        gender["Gender"]=gender["Gender"].map({"total_male":"Male","total_female":"Female"})
        st.plotly_chart(px.bar(gender,x="area_name",y="Workers",color="Gender",facet_col="mode_of_travel",facet_col_wrap=3,barmode="group",labels={"area_name":"District / UT"}),width="stretch")
        dist_cols=[c for c in view.columns if c.endswith("_persons") and c not in ["total_persons"]]
        if dist_cols:
            long=view.melt(id_vars=["area_name","residence_area","mode_of_travel"],value_vars=dist_cols,var_name="Distance band",value_name="Workers")
            long["Distance band"]=long["Distance band"].str.replace("_persons","",regex=False).str.replace("_"," ")
            st.subheader("Travel distance distribution by mode")
            st.plotly_chart(px.bar(long,x="Distance band",y="Workers",color="mode_of_travel",barmode="group",labels={"mode_of_travel":"Mode"}),width="stretch")
        st.caption("Mode shares use the source All Modes count for the same geography and residence category. They are commuter mode shares, not ride demand shares.")
elif page == "Tableau BI":
    hero("Tableau is the BI destination.", "Use the cleaned Census extract for interactive commute-mode dashboards. No booking-level metrics are supported by this source.")
    st.info("Run `python pipeline.py`, then connect Tableau to `tableau/data/census_2011_commute_modes.csv`.")
    for title,desc in [("01 · Executive Commute Overview","Urban worker counts by district, selected travel mode share and source year."),("02 · Geographic Comparison","Mode mix by Punjab district and Chandigarh; filter residence area."),("03 · Distance to Work","Counts by reported one-way distance band, mode and residence area."),("04 · Gender & Mode","Male/female/person counts by mode and distance; use the source’s aggregated values.")]: st.markdown(f"**{title}**  \n{desc}")
    st.caption("Workbook creation and publishing in Tableau Desktop/Public remain manual. The implementation guide documents calculated fields, parameters, sets, filters, actions and layout.")
elif page == "About Project":
    hero("Source and method.", "RidePulse currently integrates real public commute data as a mobility baseline.")
    st.subheader("Official sources")
    st.markdown("- Punjab workbook: [Census of India Table B-28, Punjab 2011](https://censusindia.gov.in/nada/index.php/catalog/13957) — [downloaded Excel](https://censusindia.gov.in/nada/index.php/catalog/13957/download/17070/DDW-0300B-28.xlsx).\n- Chandigarh workbook: [Census of India Table B-28, Chandigarh 2011](https://censusindia.mha.gov.in/nada/index.php/catalog/13958) — [downloaded Excel](https://censusindia.mha.gov.in/nada/index.php/catalog/13958/download/17071/DDW-0400B-28.xlsx).")
    st.write("The source is produced by the Office of the Registrar General & Census Commissioner, India. It counts ‘other workers’ by mode and one-way distance from residence to work. The extraction retains district/UT Total, Urban and Rural rows for Jalandhar, Ludhiana, Amritsar, Patiala, Sahibzada Ajit Singh Nagar (shown as Mohali district), and Chandigarh.")
    st.subheader("Important limitations")
    st.write("This is an aggregate 2011 census table, not current data and not a ride-hailing dataset. It supports commute-mode and commute-distance counts and gender breakdowns only. It has no booking IDs, pickup/drop-off points, fares, ride status, vehicle booking categories, or booking timestamps. Punjab records are district aggregates, not city proper; Mohali is represented by Sahibzada Ajit Singh Nagar district. Do not interpret auto-rickshaw/taxi commute counts as app bookings.")
