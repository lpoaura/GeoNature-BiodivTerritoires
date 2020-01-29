from sqlalchemy import Column, Integer, String, Boolean, Text
from utils_flask_sqla.serializers import serializable

from app.utils import DB


@serializable
class TaxrefProtectionArticles(DB.Model):
    __tablename__ = "taxref_protection_articles"
    __table_args__ = {"schema": "taxonomie"}
    cd_protection = Column(String, primary_key=True)
    article = Column(String)
    intitule = Column(String)
    arrete = Column(String)
    cd_arrete = Column(Integer)
    url_inpn = Column(String)
    cd_doc = Column(Integer)
    url = Column(String)
    date_arrete = Column(Integer)
    type_protection = Column(String)
    concerne_mon_territoire = Column(Boolean)

    def __repr__(self):
        return "<TaxrefProtectionArticles %r>" % self.article


@serializable
class TaxrefProtectionEspeces(DB.Model):
    __tablename__ = "taxref_protection_especes"
    __table_args__ = {"schema": "taxonomie"}
    cd_nom = Column(String, primary_key=True)
    cd_protection = Column(String, primary_key=True)
    nom_cite = Column(String)
    syn_cite = Column(String)
    nom_francais_cite = Column(String)
    precisions = Column(String)
    cd_nom_cite = Column(String, primary_key=True)


@serializable
class Taxref(DB.Model):
    __tablename__ = "taxref"
    __table_args__ = {"schema": "taxonomie"}
    cd_nom = Column(Integer, primary_key=True)
    id_statut = Column(String)
    id_habitat = Column(Integer)
    id_rang = Column(String)
    regne = Column(String)
    phylum = Column(String)
    classe = Column(String)
    regne = Column(String)
    ordre = Column(String)
    famille = Column(String)
    sous_famille = Column(String)
    tribu = Column(String)
    cd_taxsup = Column(Integer)
    cd_sup = Column(Integer)
    cd_ref = Column(Integer)
    lb_nom = Column(String)
    lb_auteur = Column(String)
    nom_complet = Column(String)
    nom_complet_html = Column(String)
    nom_vern = Column(String)
    nom_valide = Column(String)
    nom_vern_eng = Column(String)
    group1_inpn = Column(String)
    group2_inpn = Column(String)
    url = Column(String)

    def __repr__(self):
        return "<Taxref %r>" % self.nom_complet


class CorTaxonAttribut(DB.Model):
    __tablename__ = "cor_taxon_attribut"
    __table_args__ = {"schema": "taxonomie"}
    id_attribut = Column(Integer, nullable=False, primary_key=True)
    cd_ref = Column(Integer, nullable=False, primary_key=True)
    valeur_attribut = Column(Text, nullable=False)

    def __repr__(self):
        return "<CorTaxonAttribut %r>" % self.valeur_attribut


class TaxrefLR(DB.Model):
    __tablename__ = "taxref_liste_rouge_fr"
    __table_args__ = {"schema": "taxonomie"}
    id_lr = Column(Integer, primary_key=True)
    ordre_statut = Column(Integer)
    vide = Column(String)
    cd_nom = Column(Integer)
    cd_ref = Column(Integer)
    nomcite = Column(String)
    nom_scientifique = Column(String)
    auteur = Column(String)
    nom_vernaculaire = Column(String)
    nom_commun = Column(String)
    rang = Column(String)
    famille = Column(String)
    endemisme = Column(String)
    population = Column(String)
    commentaire = Column(String)
    id_categorie_france = Column(String)
    criteres_france = Column(String)
    liste_rouge = Column(String)
    fiche_espece = Column(String)
    tendance = Column(String)
    liste_rouge_source = Column(String)
    annee_publication = Column(String)
    categorie_lr_europe = Column(String)
    categorie_lr_mondiale = Column(String)


class BibRedlistCategories(DB.Model):
    __tablename__ = "bib_redlist_categories"
    __table_args__ = {"schema": "taxonomie"}
    code_category = Column(String, primary_key=True)
    threatened = Column(Boolean)
    sup_category = Column(String)
    priority_order = Column(Integer)
