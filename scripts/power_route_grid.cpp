// Deterministic four-layer A*. Native KiCad DRC remains the acceptance test.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <queue>
#include <vector>
struct Q {float f,g;int n;bool operator<(const Q& b)const{return f>b.f;}};
extern "C" int route_grid(const uint8_t* blocked,const uint8_t* via_ok,
 int w,int h,int sx,int sy,int slmask,int tx,int ty,int tlmask,int* out,int cap){
 const int plane=w*h,count=4*plane;
 std::vector<float> dist(count,INFINITY);std::vector<int> prev(count,-1);
 std::priority_queue<Q> q;
 auto heuristic=[&](int x,int y){int dx=std::abs(x-tx),dy=std::abs(y-ty);return float(std::max(dx,dy)+.41421356*std::min(dx,dy));};
 for(int l=0;l<4;l++)if(slmask&(1<<l)){int n=l*plane+sy*w+sx;if(!blocked[n]){dist[n]=0;q.push({heuristic(sx,sy),0,n});}}
 const int dxs[]={1,-1,0,0,1,1,-1,-1},dys[]={0,0,1,-1,1,-1,1,-1};
 while(!q.empty()){
  Q a=q.top();q.pop();if(a.g!=dist[a.n])continue;
  int l=a.n/plane,p=a.n%plane,x=p%w,y=p/w;
  if(x==tx&&y==ty&&(tlmask&(1<<l))){std::vector<int> path;for(int n=a.n;n>=0;n=prev[n])path.push_back(n);if(int(path.size())>cap)return -2;std::reverse(path.begin(),path.end());std::copy(path.begin(),path.end(),out);return path.size();}
  for(int k=0;k<12;k++){
   int nx=x,ny=y,nl=l;float cost;
   if(k>=8){nl=k-8;if(nl==l||!via_ok[p])continue;cost=30;}
   else{nx+=dxs[k];ny+=dys[k];if(nx<1||ny<1||nx>=w-1||ny>=h-1)continue;cost=k<4?1:1.41421356;if((l%2==0&&dxs[k]==0)||(l%2==1&&dys[k]==0))cost+=.04;if(k>=4&&(blocked[l*plane+y*w+nx]||blocked[l*plane+ny*w+x]))continue;}
   int n=nl*plane+ny*w+nx;if(blocked[n])continue;float ng=a.g+cost;if(ng<dist[n]){dist[n]=ng;prev[n]=a.n;q.push({ng+heuristic(nx,ny),ng,n});}
  }
 }
 return -1;
}
