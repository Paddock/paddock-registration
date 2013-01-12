var mod = angular.module('garage.services',['tpResource']);

mod.factory('Profile', function($resource){
  return $resource('/garage/api/v1/profile/:userId', {}, {
    query: {method:'GET', params:{userId:""}, isArray:true}
  });
});

mod.factory('Car', function($resource){
  return $resource('/garage/api/v1/car/:carId', {}, {
    query: {method:'GET', params:{carId:""}, isArray:true}
  });
});

mod.factory('Club', function($resource){
    return $resource('/garage/api/v1/club/:clubId', {}, {
      query: {method: 'GET', params:{clubId:''}, isArray:true}
    });
});