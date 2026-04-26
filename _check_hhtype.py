import pandas as pd

# Check what columns we have
df = pd.read_csv('data/9_cluster_values_k_means/k_with_values_clusters.csv', nrows=2)
print("Columns:", [c for c in df.columns if 'hh' in c.lower() or 'cluster' in c.lower() or 'ladcd' in c.lower()])

# Load with cluster and hhtype
df = pd.read_csv('data/9_cluster_values_k_means/k_with_values_clusters.csv',
                 usecols=lambda c: c in ['k_hhtype_dv', 'values_k_means_cluster', 'ladcd'])

labels = {
    1.0: "1 male 65+, no children",
    2.0: "1 female 60+, no children",
    3.0: "1 adult under PA, no children",
    4.0: "1 adult, 1 child",
    5.0: "1 adult, 2+ children",
    6.0: "Couple both under PA, no children",
    8.0: "Couple 1+ over PA, no children",
    10.0: "Couple, 1 child",
    11.0: "Couple, 2 children",
    12.0: "Couple, 3+ children",
    16.0: "2 adults not couple, both under PA, no children",
    17.0: "2 adults not couple, 1+ over PA, no children",
    18.0: "2 adults not couple, 1+ children",
    19.0: "3+ adults, no children, incl. couple",
    20.0: "3+ adults, 1-2 children, incl. couple",
    21.0: "3+ adults, 2+ children, incl. couple",
    22.0: "3+ adults, no children, EXCL couples",
    23.0: "3+ adults, 1+ children, EXCL couples",
}

print("\n--- Overall distribution ---")
counts = df['k_hhtype_dv'].value_counts().sort_index()
total = counts.sum()
for code, n in counts.items():
    print(f"{code:5.1f}  {n:6d}  {n/total*100:5.1f}%  {labels.get(code, '?')}")

print("\n--- Code 22 (3+ adults, no children, EXCL couples) by cluster ---")
c22 = df[df['k_hhtype_dv'] == 22.0]
print(f"Total code-22 rows: {len(c22)}")
cluster_col = 'values_k_means_cluster' if 'values_k_means_cluster' in df.columns else None
if cluster_col:
    for clust, grp in df.groupby(cluster_col):
        n22 = (grp['k_hhtype_dv'] == 22.0).sum()
        pct = n22 / len(grp) * 100
        print(f"  Cluster {clust}: {n22}/{len(grp)} = {pct:.1f}%")
