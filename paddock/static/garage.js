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
      url: 'paddock/api/v1/user/'+USER_ID,
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
    url: '/paddock/api/v1/car'
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
      club:"NORA-ASCC",
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
      'click .icon-edit': 'edit',
      'click #save_btn': 'save',

    },
    row_template: Handlebars.compile('<td class="view">'+
          '{{name}}</td><td class="view">{{year}} {{make}} {{model}} '+
          '<i class="icon-picture avatar_pic"'+
          'data-title="{{ name }}" href="{{ thumb }}"></i></td>'+
          '<td class="view"><i class="icon-edit"></i><i class="icon-trash"></i></td>'+ //end view, start form
          '<td class="editing"><input type="text" style="width:90%" name="name" value="{{name}}"></td>'+
          '<td class="editing"><form class="form-inline">'+
          '<input type="text" style="width:4em;" name="year" value="{{year}}">'+
          '<input type="text" style="width:35%;" name="make" value="{{make}}">'+
          '<input type="text" style="width:35%;" name="model" value="{{model}}">'+
          '</form></td>'+
          '<td class="editing"><button class="btn btn-primary" id="save_btn" style="width:6em;">Save</button></td>'),  
    initialize: function(){
      //this.model.on('change', this.render, this);
      this.model.on('destroy', this.remove, this);
      this.model.on('change', this.render, this);
    },     
    clear: function(){
      this.model.destroy();
    },
    edit: function(){
      this.$('.view, .editing').addClass('edit');
    },
    save: function(){
      var new_car = {'name':this.$('input[name="name"]').val(),
                    'year':this.$('input[name="year"]').val(),
                    'make':this.$('input[name="make"]').val(),
                    'model':this.$('input[name="model"]').val(),
                   }
      this.model.set(new_car);
      this.model.save();
      this.$('.view, .editing').removeClass('edit');
    },
    render: function(){
      var row = this.row_template(this.model.toJSON());
      this.$el.empty();
      this.$el.append(row);
      this.$('.avatar_pic').avatar_popover();
      return this;
    },
  });

  var CarsView = Backbone.View.extend({
    //el: $("#cars_table"),
    tagName:"table",
    className:"table table-striped table-bordered",
    events: {
      'click #add_car_btn': 'new_car',
    } ,      
    new_car_form: Handlebars.compile('<tr id="new_car_form"><td><input type="text" style="width:90%" name="name" placeholder="name"></td>'+
        '<td><form class="form-inline ">'+
        '<input type="text" style="width:4em;" name="year" placeholder="year">'+
        '<input type="text" style="width:35%;" name="make" placeholder="make">'+
        '<input type="text" style="width:35%;" name="model" placeholder="model">'+
        'Avatar Image: <input type="file" name="avatar">'+
        '</form></td>'+
        '<td><button class="btn btn-primary" id="add_car_btn" style="width:6em;">Add Car</button></td></tr>'), 
         
    initialize: function() {
      var c = new Car;
      var that = this;
      this.collection = new Cars();

      _(this).bindAll('add');
      this.collection.bind('add', this.add);
    },
    render: function(){
      var that = this;
      //var el = $(that.el);
      this.$el.empty();

      this.$el.append('<thead><tr><th>Name</th><th>Car</th><th></th></tr></thead>');
      _(this.collection.models).each(function(car){
        cv = new CarView({'model':car})
        that.$el.append(cv.render().el)
      });
      this.$el.append(this.new_car_form());
      return this;
    },

    add: function(car){
      this.render();
    },

    new_car: function(car){
      var name = this.$('#new_car_form input[name="name"]').val();
      var year = this.$('#new_car_form input[name="year"]').val();
      var make = this.$('#new_car_form input[name="make"]').val();
      var model = this.$('#new_car_form input[name="model"]').val();
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
    //el: $("#events_list"),
    tagName:'table',
    className:'table table-striped table-bordered',
    row_template: Handlebars.compile('<tr><td>{{club}}</td>'+
      '<td>{{name}}</td><td>{{date}}</td></tr>'),

    initialize: function(){
      this.collection = new Events([new Event, new Event, new Event]);
      this.render();
    },

    render: function(){
      var that = this;
      //var el = $(that.el);
      this.$el.empty();

      this.$el.append('<thead><tr><th>Club</th><th>Event</th><th>Date</th></tr></thead>');
      _(this.collection.models).each(function(event){
        var data = event.toJSON();
        that.$el.append(that.row_template(data));
      });
      return this;
    },
  });
  
  //main app view
  var UserView = Backbone.View.extend({
    el: $("#user_info"),
    model: new User,
    initialize: function(){
        var that = this;
        var source = $("#user_template").html();
        this.template = Handlebars.compile(source);  
        this.cars_view = new CarsView;
        this.model.fetch({
          success:function(model,response){
            that.render();
            var cars = new Cars();
            _.each(model.get('cars'),function(c){
              var car = new Car(c);
              cars.push(car);
            });
            that.cars_view.collection = cars
            that.cars_view.render();
            $('#cars_table').append(that.cars_view.el)
          },
        });
    },
    render: function(){
      var user = this.model.toJSON();
      $(this.el).append(this.template(user));
      return this;  
    }
  });
  //////////////////////////////////
  // App Setup
  //////////////////////////////////
  var user_view = new UserView;
  
  //$('#cars_table').append(cars_view.el)
  var coupons_view = new CouponsView;
  var events_view = new EventsView;
  $('#events_list').append(events_view.el)
  
})(jQuery);