from WPP_Whatsapp.api.layers.HostLayer import HostLayer


class CatalogLayer(HostLayer):

    def createProduct(self,
                      name: str, image: str, description: str, price: int, isHidden: bool,
                      url: str, retailerId: str, currency: str):
        """
           * Create a product on catalog
           * @param name Product name
           * @param image Product image
           * @param description Product description
           * @param price Product price
           * @param isHidden Product visibility
           * @param url Product url
           * @param retailerId Product own ID system
           * @param currency Product currency
           * @example
           * ```python
           * client.createtProduct(
           *    'Product name',
           *    'image in base64',
           *    'product description',
           *    '89.90',
           *    true,
           *    'https://wppconnect.io',
           *    'AKA001',
           *   );
           * ```
        """
        # ToDO:
