; ModuleID = ""
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

define i32 @"$0.add$fn"(i32 %"x", i32 %"y") 
{
entry:
  %"$res" = add i32 %"x", %"y"
  ret i32 %"$res"
}

define i32 @"$1.sub$fn"(i32 %"x", i32 %"y") 
{
entry:
  %"$res" = sub i32 %"x", %"y"
  ret i32 %"$res"
}

define i32 @"$2.main$fn"() 
{
entry:
  %"$0.x$call0$res" = call i32 @"$0.add$fn"(i32 10, i32 10)
  %"$0.x$res" = call i32 @"$1.sub$fn"(i32 %"$0.x$call0$res", i32 5)
  ret i32 %"$0.x$res"
}
