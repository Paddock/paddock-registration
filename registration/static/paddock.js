(function($) {
    $.fn.avatar_popover = function() {
        this.popover( {
            trigger: 'hover',
            content: function(){
	        var img_href = $(this).attr('href')
                return '<img src="'+img_href+'">'    
	        },
            html:true
        });
    };
})(jQuery);
