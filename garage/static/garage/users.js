var app = angular.module('users',['ngCookies','ui','tpResource','paddock.directives','garage.services'])

app.controller('user_admin', function user($scope,$cookies,Profile,Car){
    $scope.profile = Profile.get({userId:USER_ID},function(){
        var races = [];
        angular.forEach($scope.profile.upcoming_events,function(e){
            data = {id:e.id,
                    title:e.name,
                    start:e.date,
                    url:e.url,
                    club:e.club_name
                   };
            races.push(data);
        });
        
        var start_date = new Date(races[0].start);
        $('#calendar').fullCalendar({
            events: races,
            year: start_date.getFullYear(),
            month: start_date.getMonth(),
            day: start_date.getDay()}
        );
    });

    $scope.edit_car_target = null; //used to assign car to edit modal
    $scope.car_modal_show = false;

    $scope.STATIC_URL = STATIC_URL;
    $scope.avatar_url = null;
    $scope.avatar_preview = false;

    $scope.csrf = $cookies.csrftoken;

    $scope._submit_avatar_first = false;



    
    $scope.save_user = function(){
        //console.log('Saving: ',$scope.user.first_name)
        Profile.save($scope.profile);
    };

    $scope.del_car = function(car){
        //console.log(car);
        var i = $scope.profile.cars.indexOf(car);
        var car_id = $scope.profile.cars[i].id;
        //console.log(i)
        Car.remove({'carId':car_id},function(){
            $scope.profile.cars.splice(i,1);
        });
    };

    $scope.new_car = function(){
        $scope.avatar_preview = false;
        $scope.avatar_url = STATIC_URL +'garage/avatar-placeholder.png';
        $scope.car_form_title ='Add a New Car';
        $scope.edit_car_index = -1;
        var new_car = {name:null, year:null, make:null,
            model:null, provisional:true};
        Car.save(new_car,function(car){
            $scope.edit_car_target = car;
        });
        $scope.car_modal_show=true;
    };

    $scope.edit_car = function(car){
        $scope.avatar_preview = false;
        $scope.avatar_url = car.avatar;
        $scope.edit_car_index = $scope.profile.cars.indexOf(car);
        $scope.car_form_title='Edit ' + car.name;
        $scope.edit_car_target = angular.copy(car);
        $scope.car_modal_show = true;
    }

    $scope.save_car = function() {
        if($scope._submit_avatar_first) {
            avatar_form.submit(); // submits the form for the avatar file
            // success of this trigger save_car_fields
        }
        else {
            $scope.save_car_fields();
        }
        
    }

    //setup for upload preview
    $("#avatar_upload").change( function(e) {
        $scope._submit_avatar_first=true;
        var file = this.files[0];
        var reader = new FileReader();
        reader.onload = function(e) {
            $scope.$apply('avatar_preview = true');
            $('#avatar-preview').attr('src', e.target.result);
        };
        reader.readAsDataURL(file);
    });
    var avatar_form = $('#avatar_form');
    avatar_form.ajaxForm({
        success: function(resp,status,xhr,element){
          $scope.edit_car_target.avatar = resp.avatar;
          $scope.edit_car_target.thumb = resp.thumb;
          $scope.save_car_fields();
        },
        error: function(resp,status,xhr,element){
          
        },
        dataType: 'json'
    })

    $scope.save_car_fields = function() {
        $scope.edit_car_target.provisional=false;
        
        //strip any hack strings from the links
        if ($scope.edit_car_target.avatar){
            $scope.edit_car_target.avatar = $scope.edit_car_target.avatar.replace(/#[0-9]+\b/,'');
            $scope.edit_car_target.thumb =  $scope.edit_car_target.thumb.replace(/#[0-9]+\b/,'');
        }

        Car.save($scope.edit_car_target,function(car){
            if ($scope.edit_car_index<0){
                $scope.profile.cars.push(car);
            }
            else{
                $scope.profile.cars[$scope.edit_car_index] = angular.copy(car);
                //dirty hack to trick the browser to reload the images incase the changed
                $scope.profile.cars[$scope.edit_car_index].avatar = car.avatar + "#" + new Date().getTime();
                $scope.profile.cars[$scope.edit_car_index].thumb =  car.thumb + "#" + new Date().getTime();
                console.log($scope.profile.cars[$scope.edit_car_index].avatar); 
            }

            $scope.edit_car_target = null; 
            $scope.car_modal_show = false;
        });
    }

    $scope.cancel_edit_car = function(){
        if($scope.edit_car_index<0){
            Car.delete({'carId':$scope.edit_car_target.id}); //just a little cleanup so we don't have too many provisional cars around
        }
        $scope.edit_car_target = null; 
        $scope.car_modal_show=false;
    }

    
});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/users.html', controller: 'user_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);
