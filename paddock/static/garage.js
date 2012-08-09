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
      year:"1990",
      make:"Mazda",
      model:"Miata",
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
        var source = $("#user_template").html();
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
  
  var CarView = Backbone.View.extend({
    tagName:"tr",
    attributes:{colspan:'3'},
    events: {
      'click .icon-trash': 'clear',
    },
    row_template: Handlebars.compile('<td><i class="icon-picture avatar_pic" \
          data-title="{{ name }}" href="{{ thumb }}"></i> \
          {{name}}</td><td>{{year}} {{make}} {{model}}</td> \
          <td><i class="icon-edit"></i><i class="icon-trash"></i></td>'),  
    initialize: function(){
      //this.model.on('change', this.render, this);
      this.model.on('destroy', this.remove, this);
    },     
    clear: function(){
        this.model.destroy();
    },
    render: function(){
      var row = this.row_template(this.model.toJSON());
      this.$el.empty();
      this.$el.append(row);
      this.$('.avatar_pic').avatar_popover();
      return this;
    },
  });

  var CarsView = TableCollectionView.extend({
    //el: $("#cars_table"),
    tagName:"table",
    className:"table table-striped table-bordered",
    events: {
      'click .btn': 'new_car',
    } ,        
    initialize: function() {
      var c = new Car;
      var that = this;
      this.collection = new Cars([c,]);

      _(this).bindAll('add');
      this.collection.bind('add', this.add);

      this.render();
    },
    render: function(){
      var that = this;
      //var el = $(that.el);
      this.$el.empty();

      this.$el.append('<thead><tr><td>Name</td><td>Car</td><td></td></tr></thead>');
      _(this.collection.models).each(function(car){
        cv = new CarView({'model':car})
        that.$el.append(cv.render().el)
      });
      this.$el.append('<tr><td><input type="text" style="width:90%" name="name" placeholder="name"></td>'+
        '<td><form class="form-inline">'+
        '<input type="text" style="width:4em;" name="year" placeholder="year">'+
        '<input type="text" style="width:30%;" name="make" placeholder="make">'+
        '<input type="text" style="width:30%;" name="model" placeholder="model">'+
        '</form></td>'+
        '<td><button class="btn btn-primary">Add Car</button></td></tr>')
      return this;
    },

    add: function(car){
      this.render();
    },

    new_car: function(car){
      var name = this.$('input[name="name"]').val();
      var year = this.$('input[name="year"]').val();
      var make = this.$('input[name="make"]').val();
      var model = this.$('input[name="model"]').val();
      var c = new Car({'name':name, 
                       'year':year,
                       'make':make,
                       'model':model})
      this.collection.push(c);
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
    row_template: Handlebars.compile("<td>{{club}}</td>"+
      "<td>{{code}}</td> "+
      "<td>{{value}}</td>"+
      "<td>{{expiration}}</td>"+
      "<td>{{uses}}</td>"),
    initialize: function() {
      var c = new Coupon;
      this.collection = new Coupons([c,]);
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
  $('#cars_table').append(cars_view.el)
  var coupons_view = new CouponsView;
  var events_view = new EventsView;
  
})(jQuery);