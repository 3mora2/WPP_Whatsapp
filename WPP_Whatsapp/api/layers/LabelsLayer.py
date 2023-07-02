from WPP_Whatsapp.api.layers.CatalogLayer import CatalogLayer


class LabelsLayer(CatalogLayer):
    def addNewLabel(self, name, options):
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
        return self.ThreadsafeBrowser.sync_page_evaluate("""({ name, options }) => {
        WPP.labels.addNewLabel(name, options);
      }""", {"name": name, "options": options})

    def addOrRemoveLabels(self, chatIds, options):
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
        return self.ThreadsafeBrowser.sync_page_evaluate("""({ chatIds, options }) => {
        WPP.labels.addOrRemoveLabels(chatIds, options);
      }""", {"chatIds": chatIds, "options": options})

    def getAllLabels(self):
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WPP.labels.getAllLabels()")

    def getLabelById(self, Id):
        return self.ThreadsafeBrowser.sync_page_evaluate("""({ id }) => {WPP.labels.getLabelById(id); }""", {"id": Id})

    def deleteAllLabels(self):
        return self.ThreadsafeBrowser.sync_page_evaluate("""() => {WPP.labels.deleteAllLabels();}""")

    def deleteLabel(self, Id):
        return self.ThreadsafeBrowser.sync_page_evaluate("""({ id }) => {WPP.labels.deleteLabel(id); }""", {"id": Id})
