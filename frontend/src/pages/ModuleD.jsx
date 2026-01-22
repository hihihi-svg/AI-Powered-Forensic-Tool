import { useState, useEffect } from "react";
import axios from "axios";
import { Trash2, Search, Database, Eye, X, Loader } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const API_URL = "http://localhost:8086/api";
import { SessionManager } from "../config/api"; // Import SessionManager

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1'];
// const FIRST_NAMES... (keep existing)

const FIRST_NAMES = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra"];
const LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"];

const generateName = (seedStr) => {
    if (!seedStr) return "Unknown";
    // Simple hash
    let hash = 0;
    for (let i = 0; i < seedStr.length; i++) {
        hash = seedStr.charCodeAt(i) + ((hash << 5) - hash);
    }
    const fIndex = Math.abs(hash) % FIRST_NAMES.length;
    const lIndex = Math.abs(hash >> 16) % LAST_NAMES.length; // Shift for variance
    return `${FIRST_NAMES[fIndex]} ${LAST_NAMES[lIndex]}`;
};

const ModuleD = () => {
    const [suspects, setSuspects] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState("");
    const [selectedCrime, setSelectedCrime] = useState("");
    const [viewSuspect, setViewSuspect] = useState(null);

    // New Feature State
    const [showAddModal, setShowAddModal] = useState(false);
    const [showDeletedModal, setShowDeletedModal] = useState(false);
    const [deletedSuspects, setDeletedSuspects] = useState([]);
    const [newSuspectFile, setNewSuspectFile] = useState(null);
    const [newSuspectCrime, setNewSuspectCrime] = useState("Theft");
    const [newSuspectName, setNewSuspectName] = useState("");
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        loadSuspects();
        loadStats();
    }, []);

    // Calculate stats client-side whenever suspects are loaded
    useEffect(() => {
        if (suspects.length > 0) {
            const distribution = {};
            suspects.forEach(suspect => {
                const crime = suspect.payload?.crime_type || "Unknown";
                distribution[crime] = (distribution[crime] || 0) + 1;
            });

            setStats(prev => ({
                ...prev,
                total_records: suspects.length,
                crime_distribution: distribution,
                vector_size: prev?.vector_size || 512
            }));
        }
    }, [suspects]);

    const loadSuspects = async (crimeType = "") => {
        setLoading(true);
        try {
            // Load ALL records (limit 15000 to cover full dataset)
            const url = crimeType
                ? `${API_URL}/suspects?crime_type=${crimeType}&limit=15000`
                : `${API_URL}/suspects?limit=15000`;
            const response = await axios.get(url);
            setSuspects(response.data.data || []);
        } catch (error) {
            console.error("Error loading suspects:", error);
            alert("Failed to load suspects");
        } finally {
            setLoading(false);
        }
    };

    const loadStats = async () => {
        try {
            const response = await axios.get(`${API_URL}/suspects/stats/overview`);
            setStats(response.data.data);
        } catch (error) {
            console.error("Error loading stats:", error);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm("Are you sure you want to delete this suspect?")) return;

        try {
            await axios.delete(`${API_URL}/suspects/${id}`);
            alert("Suspect deleted successfully");
            loadSuspects(selectedCrime);
            loadStats();

            // Log Interaction
            SessionManager.logInteraction('delete', `Deleted suspect record: ${id}`, {
                record_id: id
            });
        } catch (error) {
            console.error("Delete error:", error);
            alert("Failed to delete suspect");
        }
    };

    const handleFilter = (crimeType) => {
        setSelectedCrime(crimeType);
        loadSuspects(crimeType);
    };




    const handleLoadDeleted = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_URL}/suspects/deleted`);
            setDeletedSuspects(response.data.data || []);
            setShowDeletedModal(true);
        } catch (error) {
            console.error("Error loading deleted suspects:", error);
            alert("Failed to load deleted suspects");
        } finally {
            setLoading(false);
        }
    };

    // New Demo Data Feature
    const [seeding, setSeeding] = useState(false);
    const [seedStatus, setSeedStatus] = useState(null);

    const handleSeedData = async () => {
        if (!confirm("This will download and index 15 sample suspects from the internet. Continue?")) return;

        try {
            setSeeding(true);
            await axios.post(`${API_URL}/system/seed-demo-data`);
            pollSeedStatus();
        } catch (error) {
            console.error("Seeding error:", error);
            alert("Failed to start data loading");
            setSeeding(false);
        }
    };

    const pollSeedStatus = async () => {
        const interval = setInterval(async () => {
            try {
                const res = await axios.get(`${API_URL}/system/seed-status`);
                setSeedStatus(res.data);

                if (res.data.status === 'completed' || res.data.status === 'failed') {
                    clearInterval(interval);
                    setSeeding(false);
                    if (res.data.status === 'completed') {
                        alert("Success! Demo data loaded.");
                        loadSuspects();
                        loadStats();
                    } else {
                        alert("Error loading data: " + res.data.message);
                    }
                    setTimeout(() => setSeedStatus(null), 3000);
                }
            } catch (e) {
                clearInterval(interval);
                setSeeding(false);
            }
        }, 1000);
    };

    const handleAddSubmit = async (e) => {
        e.preventDefault();
        if (!newSuspectFile) {
            alert("Please select an image");
            return;
        }

        setSubmitting(true);
        const formData = new FormData();
        formData.append("file", newSuspectFile);
        formData.append("crime_type", newSuspectCrime);
        formData.append("name", newSuspectName || "Unknown");

        try {
            await axios.post(`${API_URL}/suspects`, formData);
            alert("Suspect added successfully");
            setShowAddModal(false);
            setNewSuspectFile(null);
            setNewSuspectName("");
            loadSuspects(selectedCrime);
            loadStats();
        } catch (error) {
            console.error("Error adding suspect:", error);
            alert("Failed to add suspect");
        } finally {
            setSubmitting(false);
        }
    };

    const getSuspectName = (suspect) => {
        if (suspect.payload?.name && suspect.payload.name !== "Unknown") return suspect.payload.name;

        const filename = suspect.payload?.filename;
        if (!filename) return "Unknown";
        // Remove extension
        const base = filename.replace(/\.[^/.]+$/, "");
        // Extract ID before _aug
        const baseId = base.split("_aug")[0];
        return generateName(baseId);
    };

    const getBaseId = (filename) => {
        if (!filename) return "Unknown";
        const base = filename.replace(/\.[^/.]+$/, "");
        return base.split("_aug")[0];
    };

    const filteredSuspects = suspects
        .filter(suspect => {
            const filename = suspect.payload?.filename?.toLowerCase() || "";
            return filename.includes(filter.toLowerCase());
        })
        .sort((a, b) => {
            // Sort by original_index if available
            const idxA = a.payload?.original_index ?? 999999;
            const idxB = b.payload?.original_index ?? 999999;
            return idxA - idxB;
        });

    return (
        <div className="space-y-8">
            <header>
                <h2 className="text-3xl font-bold text-white mb-2">Database Management</h2>
                <p className="text-slate-400">Manage suspect records in the database</p>
            </header>

            {/* Statistics Dashboard */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-gradient-to-br from-blue-600 to-blue-700 p-6 rounded-xl border border-blue-500">
                        <div className="flex items-center gap-3">
                            <Database className="w-8 h-8 text-white" />
                            <div>
                                <p className="text-blue-100 text-sm">Total Records</p>
                                <p className="text-3xl font-bold text-white">{stats.total_records?.toLocaleString()}</p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-purple-600 to-purple-700 p-6 rounded-xl border border-purple-500">
                        <div>
                            <p className="text-purple-100 text-sm mb-2">Crime Types</p>
                            <p className="text-2xl font-bold text-white">
                                {Object.keys(stats.crime_distribution || {}).length}
                            </p>
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-green-600 to-green-700 p-6 rounded-xl border border-green-500">
                        <div>
                            <p className="text-green-100 text-sm mb-2">Vector Size</p>
                            <p className="text-2xl font-bold text-white">{stats.vector_size} dimensions</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Crime Type Distribution */}
            {stats?.crime_distribution && (
                <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-xl font-semibold text-white mb-6">Crime Type Distribution</h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                        {/* Chart */}
                        <div className="w-full" style={{ height: 300 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={Object.entries(stats.crime_distribution).map(([name, value]) => ({ name, value }))}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        paddingAngle={5}
                                        dataKey="value"
                                        label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                                    >
                                        {Object.entries(stats.crime_distribution).map((entry, index) => (
                                            <Cell
                                                key={`cell-${index}`}
                                                fill={COLORS[index % COLORS.length]}
                                                onClick={() => handleFilter(entry[0])}
                                                className="cursor-pointer hover:opacity-80 transition-opacity outline-none"
                                            />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff', borderRadius: '8px' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Legend / Filter Buttons */}
                        <div className="grid grid-cols-2 gap-4">
                            {Object.entries(stats.crime_distribution).map(([crime, count], index) => (
                                <button
                                    key={crime}
                                    onClick={() => handleFilter(crime)}
                                    className={`p-4 rounded-lg border transition-all flex items-center justify-between group ${selectedCrime === crime
                                        ? "bg-blue-600/20 border-blue-500 text-white"
                                        : "bg-slate-900 border-slate-700 text-slate-300 hover:border-blue-500 hover:bg-slate-800"
                                        }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <div
                                            className="w-3 h-3 rounded-full shadow-sm group-hover:scale-110 transition-transform"
                                            style={{ backgroundColor: COLORS[index % COLORS.length] }}
                                        />
                                        <span className="text-sm font-medium">{crime}</span>
                                    </div>
                                    <span className="text-lg font-bold">{count}</span>
                                </button>
                            ))}

                            {selectedCrime && (
                                <button
                                    onClick={() => handleFilter("")}
                                    className="col-span-2 mt-2 px-4 py-2 border border-slate-600 rounded-lg text-slate-400 hover:text-white hover:border-slate-400 text-sm transition-all"
                                >
                                    Clear Filter
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Search and Actions */}
            <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                <div className="flex gap-4 mb-4">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-3 w-5 h-5 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Search by filename..."
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                        />
                    </div>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all flex items-center gap-2"
                    >
                        <span>+</span>
                        Add Suspect
                    </button>
                    <button
                        onClick={handleLoadDeleted}
                        className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-all flex items-center gap-2 border border-slate-600"
                    >
                        <span>History</span>
                        History (Deleted)
                    </button>
                    {!seeding ? (
                        <button
                            onClick={handleSeedData}
                            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-all flex items-center gap-2"
                        >
                            <Database className="w-4 h-4" />
                            Load Demo Data
                        </button>
                    ) : (
                        <div className="px-6 py-2 bg-purple-900/50 text-purple-200 rounded-lg flex items-center gap-2 border border-purple-500/50">
                            <Loader className="w-4 h-4 animate-spin" />
                            <span className="text-xs">{seedStatus?.message || "Loading..."}</span>
                        </div>
                    )}
                </div>

                {/* Suspects Table */}
                <div className="overflow-x-auto">
                    {loading ? (
                        <div className="text-center py-12 text-slate-500">
                            Loading suspects...
                        </div>
                    ) : filteredSuspects.length === 0 ? (
                        <div className="text-center py-12 text-slate-500">
                            No suspects found
                        </div>
                    ) : (
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-slate-700">
                                    <th className="text-left py-3 px-4 text-slate-400 font-semibold">Index</th>
                                    <th className="text-left py-3 px-4 text-slate-400 font-semibold">ID</th>
                                    <th className="text-left py-3 px-4 text-slate-400 font-semibold">Name</th>
                                    <th className="text-left py-3 px-4 text-slate-400 font-semibold">Filename</th>
                                    <th className="text-left py-3 px-4 text-slate-400 font-semibold">Crime Type</th>
                                    <th className="text-left py-3 px-4 text-slate-400 font-semibold">Timestamp</th>
                                    <th className="text-right py-3 px-4 text-slate-400 font-semibold">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredSuspects.map((suspect) => (
                                    <tr key={suspect.id} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                                        <td className="py-3 px-4 text-blue-400 font-bold">
                                            {suspect.payload?.original_index ?? "—"}
                                        </td>
                                        <td className="py-3 px-4 text-slate-300 font-mono text-sm">
                                            {getBaseId(suspect.payload?.filename)}
                                        </td>
                                        <td className="py-3 px-4 text-white font-semibold text-blue-300">
                                            {getSuspectName(suspect)}
                                        </td>
                                        <td className="py-3 px-4 text-white">
                                            {suspect.payload?.filename || "Unknown"}
                                        </td>
                                        <td className="py-3 px-4">
                                            <span className="px-3 py-1 bg-orange-600/20 text-orange-400 rounded-full text-sm">
                                                {suspect.payload?.crime_type || "Unknown"}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-slate-400 text-sm">
                                            {suspect.payload?.timestamp?.split('T')[0] || "N/A"}
                                        </td>
                                        <td className="py-3 px-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => {
                                                        setViewSuspect(suspect);
                                                        // Log Interaction
                                                        SessionManager.logInteraction('view', `Viewed details: ${suspect.payload?.filename}`, {
                                                            suspect_id: suspect.id,
                                                            crime_type: suspect.payload?.crime_type
                                                        });
                                                    }}
                                                    className="p-2 text-blue-400 hover:text-blue-300 hover:bg-blue-900/20 rounded transition-all"
                                                    title="View Details"
                                                >
                                                    <Eye className="w-4 h-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(suspect.id)}
                                                    className="p-2 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded transition-all"
                                                    title="Delete"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

                <div className="mt-4 text-sm text-slate-500">
                    Showing {filteredSuspects.length} of {suspects.length} suspects
                </div>
            </div>

            {/* Metadata Modal */}
            {viewSuspect && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-lg shadow-2xl animate-in fade-in zoom-in duration-200">
                        <div className="flex items-center justify-between p-6 border-b border-slate-700">
                            <h3 className="text-xl font-bold text-white">Suspect Details</h3>
                            <button
                                onClick={() => setViewSuspect(null)}
                                className="text-slate-400 hover:text-white transition-colors"
                            >
                                <X className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="p-6 space-y-6">
                            {/* Image Display */}
                            <div className="flex justify-center bg-black/20 rounded-lg p-4 mb-4">
                                <img
                                    src={`${API_URL}/images/${viewSuspect.payload?.filename}`}
                                    alt="Suspect"
                                    className="h-64 object-contain rounded shadow-lg"
                                    onError={(e) => {
                                        e.target.onerror = null;
                                        e.target.src = "https://via.placeholder.com/300x300?text=No+Image";
                                    }}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <p className="text-sm text-slate-400">Original Index</p>
                                    <p className="text-2xl font-bold text-blue-400">
                                        {viewSuspect.payload?.original_index ?? "—"}
                                    </p>
                                </div>
                                <div className="space-y-1">
                                    <p className="text-sm text-slate-400">Filename</p>
                                    <p className="text-lg font-semibold text-white break-all">
                                        {viewSuspect.payload?.filename || "Unknown"}
                                    </p>
                                </div>
                            </div>

                            <div className="space-y-4 pt-4 border-t border-slate-700">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm text-slate-400 mb-1">Crime Type</p>
                                        <span className="px-3 py-1 bg-orange-600/20 text-orange-400 rounded-full text-sm font-medium">
                                            {viewSuspect.payload?.crime_type || "Unknown"}
                                        </span>
                                    </div>
                                    <div>
                                        <p className="text-sm text-slate-400 mb-1">Timestamp</p>
                                        <p className="text-slate-200 font-mono text-sm">
                                            {viewSuspect.payload?.timestamp || "N/A"}
                                        </p>
                                    </div>
                                </div>

                                <div>
                                    <p className="text-sm text-slate-400 mb-1">Vector ID</p>
                                    <p className="text-slate-300 font-mono text-xs bg-slate-900 p-2 rounded border border-slate-700 break-all">
                                        {viewSuspect.id}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 border-t border-slate-700 bg-slate-800/50 rounded-b-xl flex justify-end">
                            <button
                                onClick={() => setViewSuspect(null)}
                                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-all"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
            {/* Add Suspect Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md shadow-2xl animate-in fade-in zoom-in duration-200">
                        <div className="flex items-center justify-between p-6 border-b border-slate-700">
                            <h3 className="text-xl font-bold text-white">Add New Suspect</h3>
                            <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white">
                                <X className="w-6 h-6" />
                            </button>
                        </div>
                        <form onSubmit={handleAddSubmit} className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm text-slate-400 mb-2">Suspect Image</label>
                                <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center hover:border-blue-500 transition-colors cursor-pointer relative">
                                    <input
                                        type="file"
                                        onChange={(e) => setNewSuspectFile(e.target.files[0])}
                                        className="absolute inset-0 opacity-0 cursor-pointer"
                                        accept="image/*"
                                    />
                                    {newSuspectFile ? (
                                        <div className="text-green-400 font-medium break-all">
                                            {newSuspectFile.name}
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center gap-2 text-slate-400">
                                            <span>Upload</span>
                                            <span>Click to upload image</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm text-slate-400 mb-2">Suspect Name</label>
                                <input
                                    type="text"
                                    value={newSuspectName}
                                    onChange={(e) => setNewSuspectName(e.target.value)}
                                    placeholder="Enter suspect name"
                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:border-blue-500 outline-none"
                                />
                            </div>

                            <div>
                                <label className="block text-sm text-slate-400 mb-2">Crime Type</label>
                                <select
                                    value={newSuspectCrime}
                                    onChange={(e) => setNewSuspectCrime(e.target.value)}
                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:border-blue-500 outline-none"
                                >
                                    {["Theft", "Fraud", "Assault", "Burglary", "Vandalism", "Cybercrime", "Other"].map(crime => (
                                        <option key={crime} value={crime}>{crime}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="pt-4 flex justify-end gap-3">
                                <button
                                    type="button"
                                    onClick={() => setShowAddModal(false)}
                                    className="px-4 py-2 text-slate-300 hover:text-white"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={submitting}
                                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50"
                                >
                                    {submitting ? "Adding..." : "Add Suspect"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Deleted Suspects Modal */}
            {showDeletedModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-2xl shadow-2xl animate-in fade-in zoom-in duration-200">
                        <div className="flex items-center justify-between p-6 border-b border-slate-700">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                <Trash2 className="w-5 h-5 text-red-400" />
                                Recently Deleted
                            </h3>
                            <button onClick={() => setShowDeletedModal(false)} className="text-slate-400 hover:text-white">
                                <X className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="p-0 max-h-[60vh] overflow-y-auto">
                            {deletedSuspects.length === 0 ? (
                                <div className="p-8 text-center text-slate-500">
                                    Recycle bin is empty
                                </div>
                            ) : (
                                <table className="w-full">
                                    <thead className="bg-slate-900/50 sticky top-0">
                                        <tr className="text-left text-xs uppercase tracking-wider text-slate-400">
                                            <th className="p-4">ID</th>
                                            <th className="p-4">Name</th>
                                            <th className="p-4">Filename</th>
                                            <th className="p-4">Deleted At</th>
                                            <th className="p-4">Crime Type</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-700">
                                        {deletedSuspects.map((item, idx) => (
                                            <tr key={idx} className="hover:bg-slate-700/30">
                                                <td className="p-4 text-slate-300 font-mono text-sm">
                                                    {getBaseId(item.payload?.filename)}
                                                </td>
                                                <td className="p-4 text-white font-semibold text-blue-300">
                                                    {getSuspectName(item)}
                                                </td>
                                                <td className="p-4 text-slate-300 text-sm">
                                                    {item.payload?.filename || "Unknown"}
                                                </td>
                                                <td className="p-4 text-slate-400 text-sm">
                                                    {new Date(item.deleted_at).toLocaleString()}
                                                </td>
                                                <td className="p-4">
                                                    <span className="px-2 py-1 bg-slate-700 rounded text-xs text-slate-300">
                                                        {item.payload?.crime_type || "N/A"}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>

                        <div className="p-4 border-t border-slate-700 bg-slate-900/30 text-right">
                            <button
                                onClick={() => setShowDeletedModal(false)}
                                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ModuleD;
