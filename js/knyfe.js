
slugify = function(element) {
    return $(element).text().replace(/\s+/g,'-').replace(/[^a-zA-Z0-9\-]/g,'').toLowerCase().replace(/:+$/g,'');
}

$(document).ready(function() {
    $('#navbar').scrollspy();
    var blocks = []
    $("h1, h2").each(function() {
        var block = $("<div class='block'></div>")        
        var title = $(this).clone()
        title.attr("id", slugify(title))
        var content = $(this).nextUntil('h2, h1')
        // if (content.length == 0) {
        //     content = $(this).nextUntil()
        // }
        block.append(title)
        block.append(content);
        $(this).remove();
        blocks.push(block)
        var navitem = $("<li class='nav-header'><a href='#"+slugify(title)+"'>"+title.text()+"</a></li>");
        $(".nav").append(navitem)
        block.find('h3').each(function() {
            console.log($(this))
            $(this).attr('id', slugify(this));
            var navitem = $("<li><a href='#"+slugify(this)+"'>"+$(this).text().replace(/:+$/g,'')+"</a></li>");
            $(".nav").append(navitem)
        })

    })

    $(blocks).each( function() {
        $('.content').append(this);
    })

})