from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection


def geoserializable(cls):
    """
        Décorateur de classe
        Permet de rajouter la fonction as_geofeature à une classe
    """

    def serializegeofn(
        self, geoCol, idCol, recursif=False, columns=(), relationships=()
    ):
        """
        Méthode qui renvoie les données de l'objet sous la forme
        d'une Feature geojson

        Parameters
        ----------
           geoCol: string
            Nom de la colonne géométrie
           idCol: string
            Nom de la colonne primary key
           recursif: boolean
            Spécifie si on veut que les sous objet (relationship) soit
            également sérialisé
           columns: liste
            liste des columns qui doivent être prisent en compte
        """
        if not getattr(self, geoCol) is None:
            geometry = to_shape(getattr(self, geoCol))
        else:
            geometry = {"type": "Point", "coordinates": [0, 0]}

        feature = Feature(
            id=str(getattr(self, idCol)),
            geometry=geometry,
            properties=self.as_dict(recursif, columns, relationships),
        )
        return feature

    cls.as_geofeature = serializegeofn
    return cls
