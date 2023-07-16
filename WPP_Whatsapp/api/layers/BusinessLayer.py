from WPP_Whatsapp.api.layers.ControlsLayer import ControlsLayer


class BusinessLayer(ControlsLayer):
    def getBusinessProfilesProducts(self, id_: str):
        """
            * Query product catalog
            * @param id Business profile id ('00000@c.us')
        """
