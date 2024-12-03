from flask import Flask
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from kgmodel import (Foresatt, Barn, Soknad, Barnehage)
from kgcontroller import (form_to_object_soknad, insert_soknad, commit_all, select_alle_barnehager, select_alle_soknader)

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY'  # nødvendig for session


@app.route('/')
def index():
    # Hovedsiden
    return render_template('index.html')


@app.route('/barnehager')
def barnehager():
    # Viser informasjon om alle barnehager
    information = select_alle_barnehager()
    return render_template('barnehager.html', data=information)


@app.route('/behandle', methods=['GET', 'POST'])
def behandle():
    # Søknadsskjema for å sende søknad
    if request.method == 'POST':
        sd = request.form
        print(sd)
        log = insert_soknad(form_to_object_soknad(sd))
        print(log)
        session['information'] = sd
        return redirect(url_for('svar'))  # [1]
    else:
        return render_template('soknad.html')


@app.route('/svar')
def svar():
    # Behandler søknaden og gir TILBUD eller AVSLAG
    information = session['information']

    barnehage_prioritert = information.get('liste_over_barnehager_prioritert_5', '')
    fortrinnsrett = any([
        information.get('fortrinnsrett_barnevern', False),
        information.get('fortrinnsrett_sykdom_i_familien', False),
        information.get('fortrinnsrett_sykdome_paa_barnet', False)
    ])

    # Finn prioritert barnehage
    valgt_barnehage = None
    for barnehage in select_alle_barnehager():
        if barnehage.barnehage_navn == barnehage_prioritert:
            valgt_barnehage = barnehage
            break

    # Beregn resultat
    if valgt_barnehage and valgt_barnehage.barnehage_ledige_plasser > 0:
        if fortrinnsrett or valgt_barnehage.barnehage_ledige_plasser > 1:
            resultat = "TILBUD"
            # Reduser antall ledige plasser
            valgt_barnehage.barnehage_ledige_plasser -= 1
            commit_all()
        else:
            resultat = "AVSLAG"
    else:
        resultat = "AVSLAG"

    # Send resultat til svar.html
    return render_template('svar.html', data=information, resultat=resultat)


@app.route('/soknader')
def soknader():
    # Henter og viser alle søknader
    alle_soknader = []
    for soknad in select_alle_soknader():
        valgt_barnehage = None
        for barnehage in select_alle_barnehager():
            if barnehage.barnehage_navn == soknad.barnehager_prioritert:
                valgt_barnehage = barnehage
                break

        # Beregn status for søknaden
        if valgt_barnehage and valgt_barnehage.barnehage_ledige_plasser > 0:
            if soknad.fr_barnevern or soknad.fr_sykd_familie or soknad.fr_sykd_barn or valgt_barnehage.barnehage_ledige_plasser > 1:
                status = "TILBUD"
            else:
                status = "AVSLAG"
        else:
            status = "AVSLAG"

        # Legg søknaden med status i listen
        alle_soknader.append({
            'foresatt_1': soknad.foresatt_1.foresatt_navn,
            'foresatt_2': soknad.foresatt_2.foresatt_navn if soknad.foresatt_2 else "Ikke oppgitt",
            'barn': soknad.barn_1.barn_pnr,
            'prioritert_barnehage': soknad.barnehager_prioritert,
            'status': status
        })

    # Returner til soknader.html
    return render_template('soknader.html', soknader=alle_soknader)


@app.route('/commit')
def commit():
    # Lagrer alle data til databasen
    commit_all()
    return render_template('commit.html')


"""
Referanser
[1] https://stackoverflow.com/questions/21668481/difference-between-render-template-and-redirect
"""

"""
Søkeuttrykk
"""
