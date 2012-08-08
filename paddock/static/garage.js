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
      desc:"1990 Mazda Miata",
      thumb:"/media/car_thumbs/Bavikati_Maxima_avatar"
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
      club:"NORA-ASCC"
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
    collection:null,
    template: Handlebars.compile("<tr>{{{row}}}</tr>"),
    render: function() {
      var that = this;
      _.each(this.collection.models,function(item){
        var column_vals = that.row_template(item.toJSON());
        $(that.el).append(that.template({'row':column_vals}));      
      });    
    },
  });

  var TableCollectionView = CollectionView.extend({
    cols:{},
    add_form:true,
    head_row_tmp: Handlebars.compile('<th>{{name}}</th>'),
    render: function(){
      var that = this;
      var el = $(that.el)
      el.append("<thead>");
      _.each(that.cols,function(value,key){
        el.append(that.head_row_tmp({"name":value}))
      });
      el.append("</thead>")
      //hackish way to call parent's render
      TableCollectionView.__super__.render.apply(that);
    },
  });

  var ListCollectionView = CollectionView.extend({
    template: Handlebars.compile("<li>{{{row}}}</li>"),
  });
  
  var CarsView = TableCollectionView.extend({
    el: $("#cars_table"),
    cols:{"name":"Name",
          "desc":"Car",
          "":null
         },
    row_template: Handlebars.compile('<td><i class="icon-picture avatar_pic" \
            data-title="{{ name }}" href="{{ thumb }}"></i> \
            {{name}}</td><td>{{desc}}</td> \
            <td><i class="icon-edit"></i><i class="icon-trash"></i></td>'),
    
    initialize: function() {
      var c = new Car;
      this.collection = new Cars([c,c,c]);
      this.render();
    },

    render: function(){
      var that = this;
      CarsView.__super__.render.apply(that);

      $(that.el).append('<tr><td><input type="text" style="width:90%" name="name"></td> \
        <td><input type="text" style="width:90%" name="desc"></td> \
        <td><button class="btn btn-primary">Add Car</button></td> \
        </tr>')
    },
  });
  
  CouponsView = TableCollectionView.extend({
    el: $('#coupons_table'),
    add_form:false,
    cols:{'club':"Club",
             'code':"Code",
             'value':"Value",
             'expiration':'Expiration',
             'uses':"Uses Left"},
    row_template: Handlebars.compile("<td>{{club}}</td> \
      <td>{{code}}</td> \
      <td>{{value}}</td> \
      <td>{{expiration}}</td> \
      <td>{{uses}}</td>"),
    initialize: function() {
      var c = new Coupon;
      this.collection = new Coupons([c,c,c]);
      this.render();
      $(".avatar_pic").avatar_popover();
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