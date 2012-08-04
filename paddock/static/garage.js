Garage = Ember.Application.create({
    ready: function(){
        // Call the superclass's `ready` method.
        user_view.appendTo('#user_info')
        carsView.appendTo('#user_cars')
        this._super();
    }
});

/**************************
* Models
**************************/

Garage.car = Ember.Object.extend({
    name:"The Red Sea",
    color:"Red",
    year:"1990", 
    make:"Mazda",
    model:"Miata",
    avatar:"/media/car_avatars/justingray_Miata_avatar",
    thumb:"/media/car_thumbs/justingray_Miata_avatar",
});
var car1 = Garage.car.create({
    name:"The Red Sea",
    color:"Red",
    year:"1990", 
    make:"Mazda",
    model:"Miata",
    avatar:"/media/car_avatars/justingray_Miata_avatar",
    thumb:"/media/car_thumbs/justingray_Miata_avatar",
});
/**************************
* Controlers
**************************/

Garage.carsController = Ember.ArrayController.create({
   content: [car1,car1],
});

/**************************
* Views
**************************/

var user_view = Ember.View.create({
  templateName: 'user_info',
  first_name: "Justin",
  last_name: "Gray",
  email: "Justin.S.Gray@gmail.com",
  password: "xxxxxxx"
});

carsView = Ember.CollectionView.create({
  content: Garage.carController.content,
  emptyView: Ember.View.extend({
      template: Ember.Handlebars.compile("The collection is empty")
    }),
  itemViewClass: Ember.View.extend({
      template: Ember.Handlebars.compile("Testing:{{view.content.name}}")
    }),
})
