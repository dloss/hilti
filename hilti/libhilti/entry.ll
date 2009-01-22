; Startup code to transfer control from a C program to a HILTI program. 
; 
; The C program calls hilti_run() which passes control on to
; the HILTI function Main::run(). 

%__basic_frame = type { %__continuation, %__continuation, i16, i8* }
%__continuation = type { i8*, i8* }
%__frame_hilti_main = type { %__basic_frame }

declare void @hlt_main_run(%__frame_hilti_main*)

; Entry point for C program.
; Uses C calling convention. 
define ccc void @hilti_run() {

    ; Allocate dummy frame for us. 
    
    %__frame = malloc %__frame_hilti_main
       
    %cont_normal_succ = getelementptr %__frame_hilti_main* %__frame, i32 0, i32 0, i32 0, i32 0
    store i8* undef, i8** %cont_normal_succ
    %cont_normal_frame = getelementptr %__frame_hilti_main* %__frame, i32 0, i32 0, i32 0, i32 1
    store i8* undef, i8** %cont_normal_frame

    %cont_except_succ = getelementptr %__frame_hilti_main* %__frame, i32 0, i32 0, i32 1, i32 0
    store i8* undef, i8** %cont_except_succ
    %cont_except_frame = getelementptr %__frame_hilti_main* %__frame, i32 0, i32 0, i32 1, i32 1
    store i8* undef, i8** %cont_except_frame

    %exception = getelementptr %__frame_hilti_main* %__frame, i32 0, i32 0, i32 2
    store i16 undef, i16* %exception
    %exception_data = getelementptr %__frame_hilti_main* %__frame, i32 0, i32 0, i32 3
    store i8* undef, i8** %exception_data
    
    ; Allocate frame for HILTI function Main::run(). 
    
    %callee_frame = malloc %__frame_hilti_main
    
    %exit_func = bitcast void (%__basic_frame*)* @hilti_lib_exit to i8*
    %exception_func = bitcast void (%__basic_frame*)* @hilti_lib_exception to i8*
    %casted_frame = bitcast %__frame_hilti_main* %__frame to i8*

    %cont_normal_succ2 = getelementptr %__frame_hilti_main* %callee_frame, i32 0, i32 0, i32 0, i32 0
    store i8* %exit_func, i8** %cont_normal_succ2
    %cont_normal_frame2 = getelementptr %__frame_hilti_main* %callee_frame, i32 0, i32 0, i32 0, i32 1
    store i8* %casted_frame, i8** %cont_normal_frame2

    %cont_except_succ2 = getelementptr %__frame_hilti_main* %callee_frame, i32 0, i32 0, i32 0, i32 0
    store i8* %exception_func, i8** %cont_except_succ2
    %cont_except_frame2 = getelementptr %__frame_hilti_main* %callee_frame, i32 0, i32 0, i32 0, i32 1
    store i8* %casted_frame, i8** %cont_except_frame2

    %exception2 = getelementptr %__frame_hilti_main* %callee_frame, i32 0, i32 0, i32 2
    store i16 0, i16* %exception
    %exception_data2 = getelementptr %__frame_hilti_main* %callee_frame, i32 0, i32 0, i32 3
    store i8* null, i8** %exception_data

    ; Call Main::Run()
    tail call fastcc void @hlt_main_run(%__frame_hilti_main* %callee_frame)
    ret void
}

; Exit point which returns control back to C program. 
;
; Uses HILTI calling convention.

define fastcc void @hilti_lib_exit(%__basic_frame* %__frame) {
       ret void
}

; Default exception handler which prints error message and then
; passes control back to C program.
; 
; Uses HILTI calling convention.

define fastcc void @hilti_lib_exception(%__basic_frame* %__frame) {
       ; FIXME: Print something. 
       ret void
}

        
        
