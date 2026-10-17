import {PALETTE as P} from '../engine/palette.js';
import {easeOut,lerp} from '../engine/timing.js';

// Original code-native character. Coordinates are authored in a 1000×1000 local artboard.
const coat=new Path2D('M174 1000 C185 835 250 754 365 718 C430 698 455 664 466 610 L544 610 C556 666 580 699 648 719 C767 754 830 836 842 1000 Z');
const shirt=new Path2D('M391 725 C430 700 458 678 468 632 L540 632 C553 681 579 704 620 728 L573 1000 L430 1000 Z');
const neck=new Path2D('M454 646 C467 601 469 567 465 535 L543 535 C540 571 543 607 558 648 C535 687 478 687 454 646 Z');
const face=new Path2D('M351 296 C363 180 431 113 519 111 C615 111 680 189 673 315 C667 431 615 552 510 565 C414 558 351 448 351 296 Z');
const hair=new Path2D('M337 315 C304 213 353 116 455 73 C534 39 651 72 706 157 C741 211 733 298 704 357 C694 274 663 236 617 208 C633 261 626 310 610 343 C592 269 554 221 507 193 C479 242 432 280 369 303 C359 359 352 406 364 459 C326 418 313 365 337 315 Z');
const fringe=new Path2D('M363 291 C393 251 437 227 492 189 C479 270 445 324 392 350 C450 333 512 296 548 229 C556 296 542 350 518 386 C559 349 595 300 616 220 C641 280 639 337 618 390 C599 443 563 489 510 518 C448 504 398 462 371 406 C350 361 348 324 363 291 Z');
const leftEye=new Path2D('M407 369 C430 349 459 349 480 368');
const rightEye=new Path2D('M541 368 C563 349 592 350 612 370');
const mouth=new Path2D('M475 452 C495 465 521 465 541 452');
const arm=new Path2D('M634 753 C704 742 780 712 852 662 C879 643 905 655 910 679 C914 700 895 717 873 727 C799 765 735 809 670 842 Z');
const hand=new Path2D('M846 662 C873 640 908 624 936 631 C956 636 955 653 938 661 L905 675 L946 667 C967 665 971 682 951 690 L910 699 L946 698 C967 700 966 718 946 721 L895 721 C878 714 859 697 846 680 Z');

function plate(d,path,fill,tx,ty,alpha,stroke=null,width=0){d.save(()=>{d.g.translate(tx,ty);d.path(path,{fill,stroke,width,alpha})})}

export function drawGPT(d,x,y,s,{alpha=1,assemble=1,pose='listen',look=0,blink=0}={}){
  const g=d.g,a=easeOut(assemble),sep=1-a;
  d.save(()=>{
    g.translate(x,y);g.scale(s,s);
    if(pose==='think')g.rotate(-.018);else if(pose==='reply')g.rotate(.012);
    // shadow plate makes the figure feel printed, not like a flat icon.
    plate(d,coat,'rgba(23,32,51,.18)',-28*sep+12,20*sep+18,alpha*.65);
    plate(d,coat,P.ink,-120*sep,65*sep,alpha);
    plate(d,shirt,P.cobalt,78*sep,100*sep,alpha*.98);
    plate(d,neck,P.paper2,0,120*sep,alpha);
    plate(d,face,P.paper2,95*sep,45*sep,alpha);
    plate(d,hair,P.white,-65*sep,-125*sep,alpha,P.ink2,4);
    plate(d,fringe,P.cobalt2,35*sep,-70*sep,alpha*.92);

    // small four-petal clip: visual identity, deliberately not a company logo.
    const clipA=alpha*a;for(let k=0;k<4;k++){const ang=k*Math.PI/2;d.circle(690+Math.cos(ang)*21,214+Math.sin(ang)*21,14,{fill:k%2?P.gold:P.cobalt,alpha:clipA})}d.circle(690,214,9,{fill:P.white,alpha:clipA});

    // face is drawn only after plates nearly register.
    const fa=alpha*Math.max(0,(a-.45)/.55);
    if(fa>0){
      d.save(()=>{g.translate(look*10,0);g.strokeStyle=P.ink;g.lineWidth=7;g.lineCap='round';g.globalAlpha=fa*(1-blink);g.stroke(leftEye);g.stroke(rightEye);g.globalAlpha=fa;g.stroke(mouth)});
      d.circle(444+look*10,377,6,{fill:P.cobalt,alpha:fa*(1-blink)});d.circle(575+look*10,377,6,{fill:P.cobalt,alpha:fa*(1-blink)});
    }
    if(pose==='reply'){
      plate(d,arm,P.ink,180*sep,50*sep,alpha*a);
      plate(d,hand,P.paper2,220*sep,10*sep,alpha*a,P.ink2,3);
    }
    // collar and seam lines
    d.line(445,720,505,803,{color:P.paper,alpha:alpha*a*.65,width:4});d.line(564,722,505,803,{color:P.paper,alpha:alpha*a*.65,width:4});
  });
}

export function characterReveal(t,start=3.1,end=6.5){return {assemble:Math.max(0,Math.min(1,(t-start)/(end-start))),alpha:Math.max(0,Math.min(1,(t-start+.25)/.7))}}
