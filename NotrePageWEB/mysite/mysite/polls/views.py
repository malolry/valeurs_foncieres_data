from django.template import loader 
from django.shortcuts import render
from django.http import HttpResponse

import numpy as np
import pandas as pd
import plotly.express as px
import geopandas as gpd


def index(request):
    # On importe tous les fichiers nécessaires pour la création des graphes après.
    file_path = 'valeursfoncieres-2022.txt'
    region ='departements-region.csv'


    df=pd.read_csv(file_path,sep="|", decimal=",")
    #On supprime la première ligne avec les en-têtes
    df = df.drop(0)
    df = df.replace('', np.nan)
    df.drop_duplicates(subset=['No plan', 'Valeur fonciere', 'Date mutation'], keep=False, inplace=True)
    df['Code departement'] = df['Code departement'].astype(str)
    
    

    # Créer une table de correspondance entre les codes départementaux et les régions
    df_regions = pd.read_csv(region, sep=',')
    df_merged = pd.merge(df, df_regions, how='left', on='Code departement')
    
    # Définir la liste des régions à exclure
    regions_a_exclure = ['Guadeloupe', 'Martinique', 'Guyane', 'La Réunion']
    
    # Sélectionner uniquement les régions qui ne sont pas dans la liste
    df_merged = df_merged[~df_merged['region_name'].isin(regions_a_exclure)]
    
    # Sélectionner uniquement les transactions de type "Maison" ou "Appartement"
    df_reg = df[df['Type local'].isin(['Maison', 'Appartement'])]
    
    df_reg = df_merged.groupby("region_name")["Valeur fonciere"].mean().reset_index()
     
    # Chargement de la géométrie des régions
    reg_geo = gpd.read_file('reg.txt')
    
    # Fusion des données de la valeur foncière moyenne avec la géométrie des régions
    dep_map = reg_geo.merge(df_reg, left_on="nom", right_on="region_name")
    
    # POUR LE GRAPHIQUE 1
    # Affichage de la carte choroplèthe
    fig = px.choropleth_mapbox(dep_map,
                               geojson=dep_map.geometry,
                               locations=dep_map.index,
                               color="Valeur fonciere",
                               hover_name="region_name",
                               mapbox_style="carto-positron",
                               center={"lat": 47, "lon": 2},
                               zoom=5,
                               opacity=0.5,
                               )
    
    plot_html1=fig.to_html(full_html=False, default_height=550, default_width=700)
    
    
    
    
    # POUR LE GRAPHIQUE 2 
    df2=df.copy()
    mean_values = df2.groupby('Type local')['Valeur fonciere'].mean()
    
    df_mean = pd.DataFrame({'Type local': mean_values.index, 'mean_values': mean_values.values})
    
    fig = px.scatter(df_mean, 
                     x="Type local", 
                     y="mean_values", 
                     color="mean_values",
                     title = 'Coût de la surface en m²')
    
    plot_html2=fig.to_html(full_html=False, default_height=500, default_width=700)
    
   
    
    # POUR LE GRAPHIQUE 3
    # Sélectionner uniquement les transactions de type "Maison" ou "Appartement"
    df_dep = df[df['Type local'].isin(['Maison', 'Appartement'])]
    
    # Agréger les données par département et calculer la valeur foncière moyenne
    df_dep = df.groupby("Code departement")["Valeur fonciere"].mean().reset_index()
    
    # Charger la géométrie des départements
    dept_geo = gpd.read_file('dep.txt')
    
    # Fusionner les données de la valeur foncière moyenne avec la géométrie des départements
    dep_map = dept_geo.merge(df_dep, left_on="code", right_on="Code departement")
    
    # Affichage de la carte choroplèthe
    fig = px.choropleth_mapbox(dep_map,
                               geojson=dep_map.geometry,
                               locations=dep_map.index,
                               color="Valeur fonciere",
                               hover_name="Code departement",
                               mapbox_style="carto-positron",
                               center={"lat": 47, "lon": 2},
                               zoom=5,
                               opacity=0.6,
                               )
    
    plot_html3=fig.to_html(full_html=False, default_height=550, default_width=700)
    
    
    # POUR LE GRAPHIQUE 4
    df_m2 = df.copy()
    df_m2 = df_m2[df_m2['Valeur fonciere'] < 10000000]
    df_m2 = df_m2[df_m2['Valeur fonciere'] > 500]
    df_m2 = df_m2[df_m2['Type local'].isin(['Maison', 'Appartement'])]
    
    # Créer une table de correspondance entre les codes départementaux et les régions
    df_regions = pd.read_csv(region, sep=',')
    #df_merged = pd.merge(df, df_regions, how='left', on='Code departement')
    
    mean_vf = df_m2.groupby(['Code departement'])['Valeur fonciere'].mean().reset_index()
    mean_srb = df_m2.groupby(['Code departement'])['Surface reelle bati'].mean().reset_index()
    mean_st = df_m2.groupby(['Code departement'])['Surface terrain'].mean().reset_index()
    
    df_dep = pd.merge(mean_vf, mean_srb, on='Code departement')
    df_dep = pd.merge(df_dep, mean_st, on='Code departement')
    df_dep = pd.merge(df_dep, df_regions, on='Code departement')
    
    # Renommer les colonnes si nécessaire
    #df_dep.columns = ['Code departement', 'Mean Valeur fonciere', 'Mean Surface reelle bati', 'Mean Surface terrain']
    
    # Création du graphique
    fig = px.scatter(df_dep, x="Valeur fonciere", y="Surface reelle bati", size="Surface terrain", color="region_name", hover_name="Code departement",
                     log_x=True, size_max=60)
    
    # Modifier le label de l'axe x
    fig.update_layout(
        xaxis=dict(
            title="Valeur foncière moyenne",
        ),
        yaxis=dict(
            title="Surafe réelle moyenne",
        ),
        title='Comparaison des départements en fonction de leur surface réelle, valeur foncière, surface terrain et région'
    )
    plot_html4=fig.to_html(full_html=False, default_height=550, default_width=700)

    
    # Fusionner les données avec les données de correspondance
    df_merged = pd.merge(df, df_regions, how='left', on='Code departement')

    
    # Calculer les proportions de 'Type local' pour chaque 'region_name'
    df_proportions = df_merged.groupby(['region_name', 'Type local']).size().reset_index(name='count')
    df_proportions['proportion'] = df_proportions.groupby('region_name')['count'].transform(lambda x: (x / x.sum()) * 100)
    
    # Créer le graphique à barres
    fig = px.bar(df_proportions, x='proportion', y='region_name', color='Type local', 
                 barmode='stack',color_discrete_sequence=px.colors.qualitative.Pastel, orientation='h', height=600, width=900,
                 labels={'region_name': 'Région', 'proportion': 'Proportion (%)', 'Type local': 'Type local'},
                 title='Proportion des types de bien immobilier par région')
    
    plot_html5=fig.to_html(full_html=False, default_height=600, default_width=900)

    
    
    


    context = {
       'plot_html1':plot_html1,
       'plot_html3':plot_html3,
       'plot_html2':plot_html2,
       'plot_html4':plot_html4,
       'plot_html5':plot_html5}
    return render(request, "template0.html", context)

    
    

