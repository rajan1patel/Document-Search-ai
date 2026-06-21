import {defineStore} from "pinia"

import {api} from "../utils/api"



export const useAuthStore =
defineStore(
"auth",
{


state:()=>({

    user:null,

    token:null

}),



actions:{

    nitialize(){


const token =
localStorage.getItem(
"token"
)


if(token){

this.token=token

}


}

async login(
email:string,
password:string
){


const res =
await api.post(
"/auth/login",
{
email,
password
}
)



this.token =
res.data.access_token



localStorage.setItem(
"token",this.token)



},



logout(){

localStorage.removeItem(
"token"
)

this.token=null

}



}


})