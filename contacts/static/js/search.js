$(function() {

//     $('#fastsearch').keyup(function(e) {
        input = $('#fastsearch');
        var search = input.val();
        input.typeahead({source: function(query, proxy) {
            var ta = this
            $.get(input.data('url'), {q: query}, function(data){
                ta.render(data).show()
            });
        }, select: function () {
            var val = this.$menu.find('.active').data('value');
            this.$element.data('active', val);
            if(this.autoSelect || val) {
                var newVal = this.updater(val);
                this.$element
                    .val(this.displayText(newVal) || newVal)
                    .change();
                this.afterSelect(newVal);
            }
            this.hide();
            document.location.href = val['url'];
            return this;
        }});
        /*if(search != '') {
            $.get(input.data('url'), {q: search}, function(data) {
                input.typeahead({source: data});
                console.log(input);
            });
        }*/
//     });

});
