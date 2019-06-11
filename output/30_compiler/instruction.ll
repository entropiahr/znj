; ModuleID = ""
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

define i32 @"add"(i32 %"x", i32 %"y") 
{
entry:
  %".ret" = add i32 %"x", %"y"
  ret i32 %".ret"
}

define i32 @"sub"(i32 %"x", i32 %"y") 
{
entry:
  %".ret" = sub i32 %"x", %"y"
  ret i32 %".ret"
}

define i32 @"main"() 
{
entry:
  %".ret.0.call0" = call i32 @"add"(i32 10, i32 10)
  %"x" = call i32 @"sub"(i32 %".ret.0.call0", i32 5)
  ret i32 %"x"
}
