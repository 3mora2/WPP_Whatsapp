from WPP_Whatsapp.api.layers.CatalogLayer import CatalogLayer


class LabelsLayer(CatalogLayer):
    async def addNewLabel(self, name, options):
        """
          /**
           * Create New Label
           * @category Labels
           *
           * @example
           * ```javascript
           * client.addNewLabel(`Name of label`);
           * //or
           * client.addNewLabel(`Name of label`, { labelColor: '#dfaef0' });
           * //or
           * client.addNewLabel(`Name of label`, { labelColor: 4292849392 });
           * ```
           * @param name Name of label
           * @param options options of label
           */
        """
        return await self.page_evaluate("""({ name, options }) => {
        WPP.labels.addNewLabel(name, options);
      }""", {"name": name, "options": options})

    async def addOrRemoveLabels(self, chatIds, options):
        """
          /**
           * Add or delete label of chatId
           * @category Labels
           *
           * @example
           * ```javascript
           * client.addOrRemoveLabels(['[number]@c.us','[number]@c.us'],
           * [{labelId:'76', type:'add'},{labelId:'75', type:'remove'}]);
           * //or
           * ```
           * @param chatIds ChatIds
           * @param options options to remove or add
           */
        """
        return await self.page_evaluate("""({ chatIds, options }) => {
        WPP.labels.addOrRemoveLabels(chatIds, options);
      }""", {"chatIds": chatIds, "options": options})

    async def getAllLabels(self):
        return await self.page_evaluate("() => WPP.labels.getAllLabels()")

    async def getLabelById(self, Id):
        return await self.page_evaluate("""({ id }) => {WPP.labels.getLabelById(id); }""", {"id": Id})

    async def deleteAllLabels(self):
        return await self.page_evaluate("""() => {WPP.labels.deleteAllLabels();}""")

    async def deleteLabel(self, Id):
        return await self.page_evaluate("""({ id }) => {WPP.labels.deleteLabel(id); }""", {"id": Id})
