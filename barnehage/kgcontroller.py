# kgcontroller module
import pandas as pd
import numpy as np
from dbexcel import *
from kgmodel import *

# CRUD metoder

# Create
def insert_foresatt(f):
    """Setter inn en foresatt i forelder DataFrame."""
    global forelder
    new_id = 0
    if forelder.empty:
        new_id = 1
    else:
        new_id = forelder['foresatt_id'].max() + 1
    
    # Sjekk for duplikater basert på personnummer
    if not forelder[forelder['foresatt_pnr'] == f.foresatt_pnr].empty:
        return forelder  # Returner uendret hvis allerede eksisterer

    forelder = pd.concat([pd.DataFrame([[new_id,
                                         f.foresatt_navn,
                                         f.foresatt_adresse,
                                         f.foresatt_tlfnr,
                                         f.foresatt_pnr]],
                                       columns=forelder.columns), forelder], ignore_index=True)
    return forelder


def insert_barn(b):
    """Setter inn et barn i barn DataFrame."""
    global barn
    new_id = 0
    if barn.empty:
        new_id = 1
    else:
        new_id = barn['barn_id'].max() + 1

    # Sjekk for duplikater basert på personnummer
    if not barn[barn['barn_pnr'] == b.barn_pnr].empty:
        return barn  # Returner uendret hvis allerede eksisterer

    barn = pd.concat([pd.DataFrame([[new_id,
                                     b.barn_pnr]],
                                   columns=barn.columns), barn], ignore_index=True)
    return barn


def insert_soknad(s):
    """Setter inn en søknad i soknad DataFrame."""
    global soknad
    new_id = 0
    if soknad.empty:
        new_id = 1
    else:
        new_id = soknad['sok_id'].max() + 1

    soknad = pd.concat([pd.DataFrame([[new_id,
                                       s.foresatt_1.foresatt_id,
                                       s.foresatt_2.foresatt_id if s.foresatt_2 else None,
                                       s.barn_1.barn_id,
                                       s.fr_barnevern,
                                       s.fr_sykd_familie,
                                       s.fr_sykd_barn,
                                       s.fr_annet,
                                       s.barnehager_prioritert,
                                       s.sosken__i_barnehagen,
                                       s.tidspunkt_oppstart,
                                       s.brutto_inntekt]],
                                     columns=soknad.columns), soknad], ignore_index=True)
    return soknad


# ---------------------------
# Read (select)

def select_alle_barnehager():
    """Returnerer en liste med alle barnehager definert i databasen."""
    return barnehage.apply(lambda r: Barnehage(
        barnehage_id=r['barnehage_id'],
        barnehage_navn=r['barnehage_navn'],
        barnehage_antall_plasser=r['barnehage_antall_plasser'],
        barnehage_ledige_plasser=r['barnehage_ledige_plasser']
    ), axis=1).to_list()


def select_alle_soknader():
    """Returnerer en liste med alle søknader fra databasen."""
    return soknad.apply(lambda r: Soknad(
        sok_id=r['sok_id'],
        foresatt_1=Foresatt(
            foresatt_id=r['foresatt_1'],
            foresatt_navn=forelder.loc[forelder['foresatt_id'] == r['foresatt_1'], 'foresatt_navn'].values[0],
            foresatt_adresse=forelder.loc[forelder['foresatt_id'] == r['foresatt_1'], 'foresatt_adresse'].values[0],
            foresatt_tlfnr=forelder.loc[forelder['foresatt_id'] == r['foresatt_1'], 'foresatt_tlfnr'].values[0],
            foresatt_pnr=forelder.loc[forelder['foresatt_id'] == r['foresatt_1'], 'foresatt_pnr'].values[0]
        ),
        foresatt_2=Foresatt(
            foresatt_id=r['foresatt_2'],
            foresatt_navn=forelder.loc[forelder['foresatt_id'] == r['foresatt_2'], 'foresatt_navn'].values[0],
            foresatt_adresse=forelder.loc[forelder['foresatt_id'] == r['foresatt_2'], 'foresatt_adresse'].values[0],
            foresatt_tlfnr=forelder.loc[forelder['foresatt_id'] == r['foresatt_2'], 'foresatt_tlfnr'].values[0],
            foresatt_pnr=forelder.loc[forelder['foresatt_id'] == r['foresatt_2'], 'foresatt_pnr'].values[0]
        ) if not pd.isna(r['foresatt_2']) else None,
        barn_1=Barn(
            barn_id=r['barn_1'],
            barn_pnr=barn.loc[barn['barn_id'] == r['barn_1'], 'barn_pnr'].values[0]
        ),
        fr_barnevern=r['fr_barnevern'],
        fr_sykd_familie=r['fr_sykd_familie'],
        fr_sykd_barn=r['fr_sykd_barn'],
        fr_annet=r['fr_annet'],
        barnehager_prioritert=r['barnehager_prioritert'],
        sosken__i_barnehagen=r['sosken__i_barnehagen'],
        tidspunkt_oppstart=r['tidspunkt_oppstart'],
        brutto_inntekt=r['brutto_inntekt']
    ), axis=1).to_list()


def select_foresatt(f_navn):
    """Henter foresatt basert på navn."""
    series = forelder[forelder['foresatt_navn'] == f_navn]['foresatt_id']
    if series.empty:
        return np.nan
    else:
        return series.iloc[0]


def select_barn(b_pnr):
    """Henter barn basert på personnummer."""
    series = barn[barn['barn_pnr'] == b_pnr]['barn_id']
    if series.empty:
        return np.nan
    else:
        return series.iloc[0]


# ------------------
# Update


# ------------------
# Delete


# ----- Persistent lagring ------
def commit_all():
    """Skriver alle DataFrame til Excel."""
    with pd.ExcelWriter('kgdata.xlsx', mode='a', if_sheet_exists='replace') as writer:
        forelder.to_excel(writer, sheet_name='foresatt', index=False)
        barnehage.to_excel(writer, sheet_name='barnehage', index=False)
        barn.to_excel(writer, sheet_name='barn', index=False)
        soknad.to_excel(writer, sheet_name='soknad', index=False)


# --- Diverse hjelpefunksjoner ---
def form_to_object_soknad(sd):
    """Konverterer formdata til et søknadsobjekt."""
    foresatt_1 = Foresatt(0,
                          sd.get('navn_forelder_1'),
                          sd.get('adresse_forelder_1'),
                          sd.get('tlf_nr_forelder_1'),
                          sd.get('personnummer_forelder_1'))
    insert_foresatt(foresatt_1)
    foresatt_2 = Foresatt(0,
                          sd.get('navn_forelder_2'),
                          sd.get('adresse_forelder_2'),
                          sd.get('tlf_nr_forelder_2'),
                          sd.get('personnummer_forelder_2'))
    insert_foresatt(foresatt_2)
    
    foresatt_1.foresatt_id = select_foresatt(sd.get('navn_forelder_1'))
    foresatt_2.foresatt_id = select_foresatt(sd.get('navn_forelder_2'))
    
    barn_1 = Barn(0, sd.get('personnummer_barnet_1'))
    insert_barn(barn_1)
    barn_1.barn_id = select_barn(sd.get('personnummer_barnet_1'))
        
    sok_1 = Soknad(0,
                   foresatt_1,
                   foresatt_2,
                   barn_1,
                   sd.get('fortrinnsrett_barnevern'),
                   sd.get('fortrinnsrett_sykdom_i_familien'),
                   sd.get('fortrinnsrett_sykdome_paa_barnet'),
                   sd.get('fortrinssrett_annet'),
                   sd.get('liste_over_barnehager_prioritert_5'),
                   sd.get('har_sosken_som_gaar_i_barnehagen'),
                   sd.get('tidspunkt_for_oppstart'),
                   sd.get('brutto_inntekt_husholdning'))
    return sok_1
