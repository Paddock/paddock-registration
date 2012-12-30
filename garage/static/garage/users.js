var app = angular.module('users',['ui','tpResource','paddock.directives','garage.services'])

app.controller('user_admin', function user($scope,Profile,Car){
    $scope.profile = Profile.get({userId:USER_ID});

    $scope.edit_car_target = null; //used to assign car to edit modal
    $scope.car_modal_show = false;

    $scope.save_user = function(){
        //console.log('Saving: ',$scope.user.first_name)
        Profile.save($scope.profile)
    }

    $scope.del_car = function(car){
        //console.log(car);
        var i = $scope.profile.cars.indexOf(car);
        var car_id = $scope.profile.cars[i].id;
        //console.log(i)
        Car.delete({'carId':car_id},function(){
            $scope.profile.cars.splice(i,1)
        });
        
    }

    $scope.new_car = function(){
        var new_car = {name:'blank',year:'0',make:'blank',model:'blank'}
        Car.save(new_car,function(car){
            $scope.edit_car_target = car;
        })
        $scope.car_modal_show=true;
    }

    $scope.edit_car = function(car){
        $scope.edit_car_target = car;
        $scope.car_modal_show = true;
    }

    $scope.save_car = function() {
        var i = $scope.profile.cars.indexOf($scope.edit_car_target);
        Car.save($scope.edit_car_target,function(car){
            if (i<0){
                $scope.profile.cars.push(car);
            }
        });
        
        $scope.edit_car_target = null; 
        $scope.car_modal_show = false;
    }

    $scope.cancel_edit_car = function(){
        $scope.edit_car_target = null; 
        $scope.car_modal_show=false;
    }
});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/users.html', controller: 'user_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);
