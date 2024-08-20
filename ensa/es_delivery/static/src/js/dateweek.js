odoo.define('es_delivery.date_format_week', function (require) {
    "use strict";

    var FieldDateWeek = require('web.basic_fields').FieldDateTime;

    FieldDateWeek.include({
        _renderReadonly: function () {
            this._super.apply(this, arguments);
            if (["sale.order", "purchase.order","purchase.order.line", "stock.picking"].includes(this.model)) {
                if (["commitment_date", "date_planned", "sale_delivery_date"].includes(this.name)) {
                    // İlgili tarih alanının değerini al
                    var dateValue = this.recordData[this.name];
                    if (dateValue) {
                        var fieldValue = moment(dateValue).week() + " KW / " + moment(dateValue).year();
                        this.$el.text(fieldValue);
                    }
                }
            }
        }
    });
});
// düzenleme modunda
// _renderEdit: function () {
//     console.log("_renderEdit");
//     this._super.apply(this, arguments);
//     // Input alanını oluştur
//     var $input = $('<input/>', {
//         type: 'text',
//         class: 'o_input',
//         name: this.name,
//         value: this.value || '' // Orijinal değeri input alanına ekleyin
//     });
//
//     // Input alanını DOM'a ekle
//     this.$el.append($input);
// },
// okuma modunda