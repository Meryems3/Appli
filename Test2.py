#Importation des librairies

import streamlit as st
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from streamlit_option_menu import option_menu

#Création de option menu


selected = option_menu(
    menu_title='', #'Main Menu'
    options=['Tableau de référence', 'Tableau de tenors',"Courbe des taux","Paramètres de l'obligation", "Paramètres avancés"],
    icons=['table',"border-style","graph-up","card-list","bookmark-plus"],
    menu_icon='',
    orientation='vertical',
    )

#Début code

#st.sidebar.image("C:\\Users\\hp\\Downloads\\Attijariwafa_bank_logo-removebg-preview",width=300)

def is_valid_date(date_str):
    try:
        datetime.datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False

date_obj = st.sidebar.text_input("Date de la valeur (JJ/MM/AAAA) :")
data = None

if not date_obj:
    st.warning("Veuillez entrer la date de valeur !")
else:
    if not is_valid_date(date_obj):
        st.warning("La date n'est pas au format JJ/MM/AAAA. Veuillez saisir une date valide.")
    else:
        date_obj = datetime.datetime.strptime(date_obj, "%d/%m/%Y")
        
        def taux(date_obj):
            u1="https://www.bkam.ma/Marches/Principaux-indicateurs/Marche-obligataire/Marche-des-bons-de-tresor/Marche-secondaire/Taux-de-reference-des-bons-du-tresor?"

            #u2="date=24%2F02%2F2023&"

            u3="block=e1d6b9bbf87f86f8ba53e8518e882982#address-c3367fcefc5f524397748201aee5dab8-e1d6b9bbf87f86f8ba53e8518e882982"

            u21="date="

            u22=date_obj.day

            u23="%2F"

            u24=date_obj.month

            u25="%2F"

            u26=date_obj.year

            u27="&"

            u2=u21+ str(u22) + u23 + str(u24) + u25 + str(u26) + u27

            url=u1+u2+u3

            data=pd.read_html(url)

            data[0].drop(data[0].index[-1], inplace=True)

            return data[0]
        
        try:
            data = taux(date_obj)
        except Exception as e:
            st.error("Aucune donnée n'a été trouvée pour cette date.")
        
        if data is not None and not data.empty:
            if selected=='Tableau de référence':
                CT=st.container
                CT=st.subheader("Tableau des taux de référence des bons du Trésor ")
                CT=st.write("(Souce : BAM)")
                CT=st.write(data)
        
            #Manipulation du tableau 


            data["Maturité"] = pd.to_datetime(data["Date d'échéance"],format='%d/%m/%Y') - pd.to_datetime(data['Date de la valeur'],format='%d/%m/%Y')

            data["Maturité"] = data["Maturité"].dt.total_seconds().astype(float)/ (24 * 60 * 60)

            data["Maturitéa"] = data["Maturité"]/ (365)

            del data["Transaction"]

            data.rename(columns={"Date d'échéance": 'Echeance', 'Taux moyen pondéré': 'Taux', 'Date de la valeur':'Date valeur', 'Maturité':'Maturité', 'Maturitéa':'Maturité en années' }, inplace=True)

            data["Taux"] = data["Taux"].str.replace('%', '').str.replace(',', '.').astype(float)
            data["Taux"]=data["Taux"]/100
            del data["Date valeur"]


            data["TMPA"] = 0
            for i in range(0,len(data)):
                if data.at[i, 'Maturité'] < 365:
                    data.at[i, 'TMPA'] = ((1 + (data.at[i, 'Taux'] * data.at[i, 'Maturité'] / 360)) ** (365 / data.at[i, 'Maturité']) - 1)
                elif data.at[i, 'Maturité'] >= 365:
                    data.at[i, 'TMPA'] = data.at[i, 'Taux']
    
            #Année bissexticle 
            def est_bissextile(annee):
                if (annee % 4 == 0 and annee % 100 != 0) or (annee % 400 == 0):
                    return True
                else:
                    return False
            if est_bissextile(date_obj.year)==True:
                A=366
            else :
                A=365


#Méthode de bootstrap

            data= data.sort_values(by='Maturité', ascending=True)
                
            def calculate_taux_zc(data):
                S = 0
                for i in range(0,len(data)):
                    if data['Maturité en années'][i] < 1:
                        data.at[i, 'taux_zc'] = data.at[i, 'TMPA']
                    elif data['Maturité en années'][i] >= 1:
                        S = 0  
                        for j in range(0,i-1):
                            S = S + (1/((1 + data.at[j, 'taux_zc']) ** (j)))
                        data.at[i, 'taux_zc'] = (((1 + data.at[i, 'TMPA']) / (1 - data.at[i, 'TMPA'] * S)) ** (1 / i)) - 1
                return data
            data=calculate_taux_zc(data)


            def interpolation_lineaire(MJ, data,colonne):
                taux_interpole=0
                x=MJ
                if x<data['Maturité'][0]:
                    x1 = data['Maturité'][0]
                    x2 = data['Maturité'][1]
                    y1 = colonne[0]
                    y2 = colonne[1]
                    taux_interpole=y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                elif x>data['Maturité'][len(data)-1] :
                    x1 = data['Maturité'][len(data)-1]
                    x2 = data['Maturité'][len(data)-2]
                    y1 = colonne[len(data)-1]
                    y2 = colonne[len(data)-2]
                    taux_interpole=y1 + (y1 - y2) * (x - x1) / (x1 - x2)      
                else :
                    for i in range(len(data['Maturité']) - 1):
                        if x==data['Maturité'][i]:
                            taux_interpole = data['Taux'][i]
                        elif data['Maturité'][i] <= MJ < data['Maturité'][i + 1]:
                            if data['Maturité'][i]<365 and data['Maturité'][i + 1]>365 :
                                x1 = data['Maturité'][i]
                                x2 = data['Maturité'][i + 1]
                                y1 = data['TMPA'][i]
                                y2 = data['TMPA'][i + 1]
                                taux_interpole = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                            else :
                                x1 = data['Maturité'][i]
                                x2 = data['Maturité'][i + 1]
                                y1 = colonne[i]
                                y2 = colonne[i + 1]
                                taux_interpole = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                                

                return taux_interpole


            ##Création de base de données des tenors standards

            fd = pd.DataFrame({'Maturité': ['JJ', '13 sem', '26sem', '52sem', '1an', '2ans', '3ans', '4ans', '5ans', '6ans', '7ans', '8ans', '9ans', '10ans', '11ans', '12ans', '13ans', '14ans', '15ans', '16ans', '17ans', '18ans', '19ans', '20ans', '21ans', '22ans', '23ans', '24ans', '25ans', '26ans', '27ans', '28ans', '29ans', '30ans'],'Maturité en jours': [1, 91, 182, 364, 365, 731, 1096, 1461, 1826, 2192, 2557, 2922, 3287, 3653, 4018, 4383, 4748, 5114, 5479, 5844, 6209, 6575, 6940, 7305, 7670, 8036, 8401, 8766, 9131, 9497, 9862, 10227, 10592, 10958]})
            fd['Taux de rendement'] = fd['Maturité en jours'].apply(lambda maturite: interpolation_lineaire(maturite, data, data['Taux']))
            fd['Taux zéro-coupon'] = fd['Maturité en jours'].apply(lambda maturite: interpolation_lineaire(maturite,data,data['taux_zc']))
            if selected == 'Tableau de tenors':
                CT=st.container
                CT=st.write(fd)

            #Graphique
            if selected=="Courbe des taux":
                st.write("Courbe des taux de rendement en fonction des maturités en jours :")
                new=pd.DataFrame(fd)
                new = pd.DataFrame({
                    'Maturité en jours': fd['Maturité en jours'],
                    'Taux de rendement': fd['Taux de rendement'],
                    })
                st.line_chart(new.set_index('Maturité en jours'))
                st.write("Courbe des taux zéro-coupon en fonction des maturités en jours :")
                new2=pd.DataFrame(fd)
                new2 = pd.DataFrame({
                    'Maturité en jours': fd['Maturité en jours'],
                    'Taux zéro-coupon': fd['Taux zéro-coupon'],
                    })
                st.line_chart(new2.set_index('Maturité en jours'))
                a=st.button("Fusionner les deux courbes")
                if a==True :
                    new3=pd.DataFrame(fd)
                    new3 = pd.DataFrame({
                        'Maturité en jours': fd['Maturité en jours'],
                        'Taux de rendement': fd['Taux de rendement'],
                        'Taux zéro-coupon': fd['Taux zéro-coupon'],
                        })
                    st.line_chart(new3.set_index('Maturité en jours'))
                    b=st.button("Cacher la courbe fusionnée")
                    if b==True :
                        new3 = 0
              

##date emission 

date_emission=st.sidebar.text_input("Date d'émission de l'obligation (JJ/MM/AAAA)")
if selected=="Paramètres avancés" or selected=="Paramètres de l'obligation":
    if not date_emission:
        st.warning("Veuillez entrer la date d'émission.")
    else:
        if not is_valid_date(date_emission):
            st.error("Veuillez saisir une date d'émission valide et de la forme JJ/MM/AAAA.")
        else:
            date_emission = datetime.datetime.strptime(date_emission, "%d/%m/%Y")

##date echeance 

date_echeance=st.sidebar.text_input("Date d'échéance de l'obligation (JJ/MM/AAAA)")
if selected=="Paramètres avancés" or selected=="Paramètres de l'obligation":
    if not date_echeance :
        st.warning("Veuillez entrer la date d'échéance.")
    else:
        if not is_valid_date(date_echeance) or ((datetime.datetime.strptime(date_echeance, "%d/%m/%Y"))<date_emission):
            st.error("Veuillez saisir une date d'échéance valide et de la forme JJ/MM/AAAA.")
        else:
            date_echeance = datetime.datetime.strptime(date_echeance, "%d/%m/%Y")

            #Calcul de taux de rendement

            MJ = (date_echeance-date_obj).days
            taux_inter = interpolation_lineaire(MJ, data,data['Taux'])
            
            
            #Calcul de taux zc

            taux_inter2 = interpolation_lineaire(MJ, data,data['taux_zc'])

            if selected=="Paramètres de l'obligation":            
                st.write("Maturité résiduelle (jours) :")
                st.code(MJ)
                st.write("Taux de rendement :")
                st.code(taux_inter)
                st.write("Taux Zéro coupon :")
                st.code(taux_inter2)



#Valorisation        

#date jouissance 
date_jouissance = st.sidebar.text_input("Date de jouissance (JJ/MM/AAAA):")

#Taux facial
tf=st.sidebar.number_input("Taux facial de l'obligation (en %)")
tf=tf/100

#Nominal
N=st.sidebar.number_input("Nominal",100000)

if selected=="Paramètres avancés" or selected=="Paramètres de l'obligation":
    if not date_jouissance:
        st.warning("Veuillez entrer la date de jouissance.")
    else:
        if not is_valid_date(date_jouissance) or ((datetime.datetime.strptime(date_jouissance, "%d/%m/%Y"))>date_echeance) or ((datetime.datetime.strptime(date_jouissance, "%d/%m/%Y"))<date_emission):
            st.error("Veuillez saisir une date de jouissance valide de la forme JJ/MM/AAAA.")
        else:
            date_jouissance = datetime.datetime.strptime(date_jouissance, "%d/%m/%Y")
            ##date dernier coupon

            date_derniercoupon=None
            if date_obj < date_jouissance:
                date_derniercoupon = date_jouissance
            else:
                if date_obj.year == date_jouissance.year:
                    date_derniercoupon = date_jouissance
                else:
                    if (date_obj.month < date_jouissance.month or (date_obj.month == date_jouissance.month and date_obj.day < date_jouissance.day)):
                        date_derniercoupon = date_jouissance.replace(year=date_obj.year - 1)
                    else:
                        date_derniercoupon = date_jouissance.replace(year=date_obj.year)

            Mj=(date_obj-date_derniercoupon).days

            #Prochain coupon
            date_prochaincoupon=None
            if date_obj < date_jouissance:
                date_prochaincoupon=date_jouissance
            else :
                date_prochaincoupon = date_derniercoupon.replace(year=date_derniercoupon.year + 1)
            nj=(date_prochaincoupon-date_obj).days

            #Flux restants 

            F=date_echeance.year-date_derniercoupon.year
        
            #Ligne postérieure
            ligne_post=1
            if date_emission==date_jouissance:
                ligne_post=0


            #date detachement premier coupon
            date_1C=0
            date_1C=date_jouissance.replace(year=date_jouissance.year + 1)
            
            #Maturité initiale
            Mi=(date_echeance-date_emission).days
            if selected=="Paramètres avancés":
                st.write("Maturité initiale de l'obligation")
                st.code(Mi)
                st.write("Date de détachement du premier coupon")
                st.code(date_1C.strftime('%d-%m-%Y'))
                st.write("Date du prochain coupon")
                st.code(date_prochaincoupon.strftime('%d-%m-%Y'))
                st.write("Date du dernier coupon")
                st.code(date_derniercoupon.strftime('%d-%m-%Y'))
                st.write("Nombre de flux restants")
                st.code(F)      
              
            #Dirty Price
            dirty_price=0
            if Mi < 365 :
                dirty_price=N*((1+tf*Mi/360)/((1+taux_inter*MJ)/360))
            elif Mi >= 365 and MJ<365 and ligne_post==0:
                dirty_price=N*((1+tf)/(1+taux_inter*(MJ/360)))
            elif Mi >= 365 and MJ<365 and ligne_post==1 :
                dirty_price=N*((1+tf*Mi/A))/(1+taux_inter*(MJ/360))
            elif Mi >= 365 and MJ>=365 and ligne_post==0 :
                S = 0
                for j in range(1, F+1):
                    S = S + (tf/((1+taux_inter)**(j-1)))
                dirty_price=N/((1+taux_inter)**(nj/A))*(S+(1/((1+taux_inter)**(F-1))))
            elif Mi >= 365 and MJ>=365 and ligne_post==1 and F==1:
                dirty_price=N*((1+tf*(Mi/A))/(1+taux_inter)**(nj/A))
            elif Mi >= 365 and MJ>=365 and ligne_post==1 and F>1 :
                if date_obj<date_1C :
                    S1=0
                    for j in range(2, F+1):
                        S1 = S1 + (tf/((1+taux_inter)**(j-1)))
                        S2 = tf*((date_1C-date_emission)/A)
                        S3=1/((1+taux_inter)**(F-1))
                        fact= N/(1+taux_inter**(nj/A))
                        dirty_price= fact*(S1+S2+S3)
                else :
                    S = 0
                    for j in range(1, F+1):
                        S = S + (tf/((1+taux_inter)**(j-1)))
                    dirty_price=N/((1+taux_inter)**(nj/A))*(S+(1/((1+taux_inter)**(F-1))))


            #Coupon couru

            NCC=(date_obj-date_derniercoupon).days
            NDR=(date_prochaincoupon-date_obj).days
            if selected=="Paramètres avancés":
                st.write("Nombre de jours écoulés depuis le dernier coupon")
                st.code(NCC)
                st.write("Nombre de jours restants au prochain coupon")
                st.code(NDR)
            coupon_couru=N*tf*NCC/A
            #Clean price 
            clean_price=dirty_price-coupon_couru


    #affichage des prix
    if selected=="Paramètres de l'obligation":
        if not tf :
            st.warning("Veuillez saisir le taux facial de l'obligation")
        else :
            st.write("Dirty price :")
            st.code(dirty_price)
            st.write("Prix du coupon couru :")
            st.code(coupon_couru)
            st.write("Clean price :")
            st.code(clean_price)
        st.info("Veillez changer le nominal si vous voulez !")

        