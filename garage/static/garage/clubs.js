var app = angular.module('clubs',['ngCookies', 'ui', 'tpResource',
    'paddock.directives', 'garage.services', 'ngGrid']);

app.controller('club_admin', function club_admin($scope, $cookies, $http,
    Profile,Club,Season,Event,Membership,Coupon,RaceClass){

    $scope.csrf = $cookies.csrftoken;
    $scope.selected_members = [];
    $scope.selected_class = [];
    $scope.edit_membership = false;
    $scope.membersGridOptions = { data: 'memberships',
      selectedItems: $scope.selected_members,
      showColumnMenu: false,
      columnDefs: [ {field:'num', displayName:'#', width: '50px'},
          {field:'username', displayName:'User'},
          {field: 'real_name', displayName: 'Name'}
      ]
    };
    var check_tmpl = '<div class="ngCellText colt{{$index}}"><i ui-if="row.getProperty(col.field)" class="icon-ok"></i></div>';
    $scope.edit_raceclass_target = null;
    $scope.raceclassGridOptions = {
        data: 'race_classes',
        multiSelect:false,
        showColumnMenu: false,
        showFilter: false,
        displaySelectionCheckbox: false,
        selectedItems: $scope.selected_class,
        columnDefs: [
          {field:'abrv', displayName:'Class'},
          {field:'pax', displayName:'Index'},
          {field: 'pax_class', displayName: 'PAX',
          width:'45px',
          cellTemplate: check_tmpl
          },
          {field: 'bump_class', displayName: 'BMP',
          width:'45px',
          cellTemplate: check_tmpl,
          keepLastSelected: false
          }
        ],
        filterOptions: {filterText:'classSearchStr', useExternalFilter: false},
        beforeSelectionChange: function(rowItem, event){
            if (!rowItem.selected){ //for some reason, this seems backwards.
                $scope.edit_raceclass_target = rowItem.entity;
            }
            else {
                $scope.edit_raceclass_target = null;
            }
            return true;
        }
    };

    $scope.profile = Profile.get({userId:USER_ID},function(){
        //console.log($scope.profile);
    });

    $scope.club = Club.get({clubId:CLUB_ID},function(){
        //console.log($scope.club);
        $scope.location_map = {};
        angular.forEach($scope.club.locations,function(l,index){
            $scope.location_map[l.resource_uri] = index;
        });
        $scope.new_event_season = $scope.club.seasons[0];


        angular.forEach($scope.club.seasons,function(season,index){
            $scope.$watch('club.seasons['+index+'].drop_lowest_events',function(newVal,oldVal){
                //console.log($scope.club.seasons[index]);
                Season.save($scope.club.seasons[index]);
            });

        });

        $scope.memberships = $scope.club.memberships;

        $scope.coupons = $scope.club.coupons;

        $scope.race_classes = $scope.club.race_classes;
    });

    $scope.show_edit_event = false;
    $scope.default_reg_close = true;

    $scope.new_season = function(){
        var year = $scope.club.seasons[0].year + 1;
        Season.save({year:year,
                club:$scope.club.resource_uri,
                events:[]
            },
            function(new_season){
                $scope.club.seasons.unshift(new_season);
                $scope.new_event_season = $scope.club.seasons[0];
            });
        
    };

    $scope.upload_results = function(event){

    };

    $scope.delete_event = function(season,event) {
        if(confirm("You're about to delete "+event.name+". You will lose all the event data, including results!" )){
            
            Event.delete({'eventId':event.id}, function(){
                var i = season.events.indexOf(event);
                season.events.splice(i,1);
            });
        }
    };

    $scope.build_event_msg = function(event) {
        $scope.event_msg_target = event;
        $scope.show_event_msg_modal = true;
    };

    $scope.send_event_msg = function(event) {
        $http({method:'POST',url:'/garage/event/'+event.id+'/email_drivers',
            data:$.param({'subject':$scope.event_msg_subject,
                'body':$scope.event_msg_body}),
            headers:{'X-CSRFToken':$scope.csrf}
        });
        $scope.show_event_msg_modal = false;
    };

    $scope.edit_event = function(event) {
        $scope.edit_event_target = angular.copy(event);
        $scope.event_modal_title = 'Edit ' + event.name;
        $scope.edit_event_target.date = new Date(event.date);
        $scope.edit_event_target.reg_close = new Date(event.reg_close);
        $scope.edit_event_location = event.location;
        $scope.show_event_modal = true;
    };

    $scope.new_event = function(season) {
        $scope.edit_event_target = {season:season};
        $scope.event_modal_title = 'New Event';
        $scope.default_reg_close = true;
        $scope.show_event_modal = true;
    };

    $scope.cancel_save_event = function(){
        $scope.show_event_modal = false;
    };

    $scope.save_event = function(){
        if($scope.default_reg_close){
            var d = $scope.edit_event_target.date;

            // get sets it to the first hour of the day
            var midnight = new Date(d.getFullYear(),
                d.getMonth(), d.getDate());
            
            $scope.edit_event_target.reg_close = midnight;
        }
        var i = $scope.location_map[$scope.edit_event_location];
        $scope.edit_event_target.location = $scope.club.locations[i].resource_uri;
        $scope.show_event_modal = false;

        //don't need to manually update the data, because angular seems
        //to re-load it at the end of the save from the modal
        Event.save($scope.edit_event_target);
    };

    $scope.save_club_info = function(){
        Club.save($scope.club);
    };

    $scope.new_membership = function(username) {
        $http.post('/garage/clubs/'+$scope.club.safe_name+'/membership/',
            data=$.param({'username':username}),
            config={headers: {'X-CSRFToken':$scope.csrf}}).success(function(membership){
                var l = $scope.club.memberships.length;
                var index = -1;
                for (var i = 0; i < l; i++) {
                    if ($scope.club.memberships[i].id == membership.id){
                        index = i;
                        break;
                    }
                }
                if (index < 0){
                    $scope.club.memberships.push(membership);
                }
                $scope.selected_members.push(membership);
            });
    };

    $scope.save_membership = function(membership) {
        Membership.save(membership);
    };

    $scope.save_coupon = function(coupon) {
        Coupon.save(coupon);
    };

    $scope.delete_coupon = function(coupon) {
        Coupon.delete({'couponId':coupon.id}, function(){
            var i = $scope.coupons.indexOf(coupon);
            $scope.coupons.splice(i,1);
        });
    };


    $scope.save_raceclass = function(race_class) {
        console.log("TEST");
        RaceClass.save(race_class);
    };

});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/clubs.html',
        controller: 'club_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);
