$(function() {
    var max_height = 150;
    $('.readmore').each(function() {
        var el_height = $(this).height();
        if(el_height > max_height) {
            console.log($(this).text(), el_height);
            //debugger;
            var readmore_link = $('<div/>', {class: 'readmore-link text-center'});
            readmore_link.append($('<a>Lire plus</a>'));
            $(this).data('height', el_height + readmore_link.height());
            var speed = (el_height + readmore_link.height()) - max_height;;
            $(this).data('speed', speed);
            $(this).height(max_height);
            $(this).append(readmore_link);
        }
    });

    $('body').on('click', '.readmore-link', function(ev) {
        var el = $(this).parent();
        debugger;
        el.animate({height: el.data('height')}, el.data('speed'));
        $(this).removeClass('readmore-link').addClass('readless-link');
        $('a', this).text('Lire moins');
    });

    $('body').on('click', '.readless-link', function(ev) {
        var el = $(this).parent();
        el.animate({height: max_height}, el.data('speed'));
        $(this).removeClass('readless-link').addClass('readmore-link');
        $('a', this).text('Lire plus');
    });
});
