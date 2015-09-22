$(function() {
    $('.search-form').submit(function(ev) {
        var form = $(this);
        var form_values = $(this).serializeArray();
        form_values.forEach(function(field) {
            if(field['value'] == '') {
                var field_el = $('[name="'+field['name']+'"]', form);
                field_el.removeAttr('name');
            }
        });
    });
});

