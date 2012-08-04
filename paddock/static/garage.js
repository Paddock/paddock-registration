(function($){

  var Car = Backbone.Model.extend({
    defaults:{
      name:"The Red Sea",  
      desc:"1990 Mazda Miata"
    },
  });
  
  var User = Backbone.Model.extend({
  
      defaults: {
          first_name:"Justin",
          last_name:"Gray",
          email:"justin.s.gray@gmail.com"
      },
      
  });
  
  var UserView = Backbone.View.extend({
    el: $("#user_info"),
    model: new User,
    initialize: function(){
        var source = $("#user_view").html();
        this.template = Handlebars.compile(source);  
        this.render();
    },
    render: function(){
      var user = this.model.toJSON();
      $(this.el).append(this.template(user));
      return this;  
    }
  });

  var user_view = new UserView;
})(jQuery);