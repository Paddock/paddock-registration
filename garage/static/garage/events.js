var app = angular.module('events',['ngCookies', 'ui', 'tpResource',
    'paddock.directives', 'garage.services', 'ngGrid']);

function setdefault(obj,key,default_value) {
    if (obj.hasOwnProperty(key)){
        return obj[key];
    }
    else {
        return default_value;
    }
}

app.controller('event_admin', function club_admin($scope, $cookies, $http, $q, 
    Event, Session){

    $scope.csrf = $cookies.csrftoken;
    $scope.assign_username = null;

    function get_event(){
        $scope.event = Event.get({eventId:EVENT_ID},function(){
            $scope.regs = $scope.event.regs;
            $scope.reg_sets = {};
            $scope.reg_class_map = {};
            for(var i in $scope.regs) {
                var reg = $scope.regs[i];
                var key;
                if (reg.pax_class) {
                    key = reg.pax_class.name;
                    $scope.reg_class_map[key] = reg.pax_class;
                    $scope.reg_sets[key] = setdefault($scope.reg_sets, key, []);
                    $scope.reg_sets[key].push(reg);
                }
                else if (reg.bump_class) {
                    key = reg.bump_class.name;
                    $scope.reg_class_map[key] = reg.bump_class;
                    $scope.reg_sets[key] = setdefault($scope.reg_sets, key, []);
                    $scope.reg_sets[key].push(reg);
                }
                else {
                    key = 'Open Class';
                    //console.log(reg);
                    $scope.reg_sets[key] = setdefault($scope.reg_sets, key, []);
                    $scope.reg_class_map[reg.race_class.name] = reg.race_class;
                    $scope.reg_sets[key].push(reg);
                }
            }
            //console.log($scope.reg_sets);

        });
    }

    get_event();

    $scope.del_session = function(session) {
        if(confirm("You're about to delete "+session.name+". You will lose all the result data, including all times for it!" )){
            Session.remove({'sessId':session.id}, function(){
                get_event();
            });
        }
    };

    $scope.upload_status = "";
    $scope.upload_err_msg = "";
    $('#session_form').ajaxForm({
        success: function(resp,status,xhr,element){
          //console.log('Yay! Good Job!');
          $scope.$apply('upload_status = "";');
          $scope.$apply('upload_err_msg = "";');
          element.resetForm();
        },
        error: function(resp,status,xhr,element){
          var err = angular.fromJson(resp.responseText);
          var msg = "";
          for (var key in err) {
            msg += key+": "+err[key];
          }
          $scope.$apply('upload_status = "error";');
          $scope.$apply('upload_err_msg = "'+msg+'";');
          //console.log(msg);
        },
        dataType: 'json'
    });

    $scope.set_reg_driver = function(reg,username){
        data = $.param({'username':username});
        addr = '/garage/reg/'+reg.id+'/driver';
        //console.log(addr, data);

        var deferred = $q.defer();
        $http({
            url:'/garage/reg/'+reg.id+'/driver',
            method: 'POST',
            data:$.param({'username':username}),
            headers: {'X-CSRFToken':$scope.csrf, 
                      'Content-Type': 'application/x-www-form-urlencoded'}
        }).success(function(new_reg){
            console.log(new_reg);
            deferred.resolve(new_reg);

            var key;
            if (reg.pax_class) {
                key = reg.pax_class.name;
            }   
            else if (reg.bump_class) {
                key = reg.bump_class.name;
            }   
            else {
                key = 'Open Class';
            }
            var index = $scope.reg_sets[key].indexOf(reg);
            console.log(index);
            $scope.reg_sets[key][index] = new_reg;

        }).error(function(){
            console.log("bad User Name");
            deferred.reject("Invalid username");
        });


        return deferred.promise
    };
});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/events.html',
        controller: 'event_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);
