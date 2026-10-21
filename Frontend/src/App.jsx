/*
=====================================================

Adaptive Context Intelligence Engine (ACIE)

Main Application Shell

Features:
- Dashboard layout
- Sidebar navigation
- Navbar
- Page routing
- Glass UI
- Page animations

=====================================================
*/


import {

    BrowserRouter,

    Routes,

    Route,

    useLocation

} from "react-router-dom";


import {

    AnimatePresence,

    motion

} from "framer-motion";


import Navbar from "./components/Navbar";

import Sidebar from "./components/Sidebar";



import Dashboard from "./pages/Dashboard";

import Chat from "./pages/Chat";

import Memory from "./pages/Memory";

import Evaluation from "./pages/Evaluation";



import "./App.css";







function Layout(){



    const location = useLocation();





    return (



        <div className="app-layout">





            {/* Sidebar */}


            <Sidebar />









            <div className="main-area">





                {/* Navbar */}


                <Navbar />









                {/* Page Content */}


                <AnimatePresence mode="wait">



                    <motion.main



                        key={location.pathname}



                        className="page-container"



                        initial={{

                            opacity:0,

                            y:20

                        }}



                        animate={{

                            opacity:1,

                            y:0

                        }}



                        exit={{

                            opacity:0,

                            y:-20

                        }}



                        transition={{


                            duration:0.35


                        }}



                    >





                        <Routes>





                            <Route

                                path="/"

                                element={<Dashboard />}

                            />






                            <Route

                                path="/chat"

                                element={<Chat />}

                            />






                            <Route

                                path="/memory"

                                element={<Memory />}

                            />






                            <Route

                                path="/evaluation"

                                element={<Evaluation />}

                            />







                            {/* Future Settings Page */}


                            <Route

                                path="/settings"

                                element={


                                    <div>


                                        <h1>

                                            Agent Settings

                                        </h1>



                                        <p>

                                            Configuration panel coming soon.

                                        </p>


                                    </div>


                                }

                            />






                            {/* 404 */}


                            <Route

                                path="*"

                                element={


                                    <div>


                                        <h1>

                                            Page Not Found

                                        </h1>


                                    </div>


                                }

                            />





                        </Routes>





                    </motion.main>




                </AnimatePresence>





            </div>




        </div>



    );



}









function App(){



    return (



        <BrowserRouter basename={import.meta.env.BASE_URL}>


            <Layout />


        </BrowserRouter>



    );



}





export default App;
