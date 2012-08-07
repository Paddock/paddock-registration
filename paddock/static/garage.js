(function($){

  //////////////////////////////////
  // Models
  //////////////////////////////////
  var User = Backbone.Model.extend({
  
      defaults: {
          first_name:"Justin",
          last_name:"Gray",
          email:"justin.s.gray@gmail.com"
      },
      
  });
  

  var Car = Backbone.Model.extend({
    defaults:{
      name:"The Red Sea",  
      desc:"1990 Mazda Miata"
    },
  });
  
  var Cars = Backbone.Collection.extend({
    model: Car,
  });
  
  var Coupon = Backbone.Model.extend({
    defaults:{
      code:"xxxx",
      value:"0.00",
      expiration:"N/A",
      uses:"N/A",
    },
  });
  
  var Coupons = Backbone.Collection.extend({
    model: Coupon,  
  });

  var Event = Backbone.Model.extend({
    defaults:{
      name:"Auto-x",
      date:"01/01/01",
      registered:false,
    },
  });

  var Events = Backbone.Collection.extend({
    model: Event,
  });
  
  //////////////////////////////////
  // Views
  //////////////////////////////////
  
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
  
  var CollectionView  = Backbone.View.extend({
    template: Handlebars.compile("<tr>{{{row}}}</tr>"),
    render: function() {
      var that = this;
      _.each(that.collection.models,function(item){
        var columns = that.row_template(item.toJSON());
        $(that.el).append(that.template({'row':columns}));      
      });    
    },
  });

  var TableCollectionView = CollectionView;

  var ListCollectionView = CollectionView.extend({
    template: Handlebars.compile("<li>{{{row}}}</li>"),
  });
  
  CarsView = TableCollectionView.extend({
    el: $("#cars_table"),
    row_template: Handlebars.compile("<td>{{name}}</td><td>{{desc}}</td>"),
    
    initialize: function() {
      var c = new Car;
      this.collection = new Cars([c,c,c]);
      this.render();
    }
  });
  
  CouponsView = TableCollectionView.extend({
    el: $('#coupons_table'),
    row_template: Handlebars.compile("<td>{{code}}</td><td>{{value}}</td><td>{{expiration}}</td><td>{{uses}}</td>"),
    initialize: function() {
      var c = new Coupon;
      this.collection = new Coupons([c,c,c]);
      this.render();
    }
  });

  EventsView = ListCollectionView.extend({
    el: $("#events_list"),
    row_template: Handlebars.compile("{{name}}, {{date}}"),
    initialize: function(){
      this.collection = new Events([new Event, new Event, new Event]);
      this.render();
    },
  });


  
  
  
  //////////////////////////////////
  // App Setup
  //////////////////////////////////
  var user_view = new UserView;
  var cars_view = new CarsView;
  var coupons_view = new CouponsView;
  var events_view = new EventsView;
  
})(jQuery);